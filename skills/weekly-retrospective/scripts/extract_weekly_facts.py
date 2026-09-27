#!/usr/bin/env python3
"""Extract record metadata for review; does not verify evidence or scientific claims."""
import argparse
from datetime import date, datetime
import json
from pathlib import Path
import re
import sys

RELATIONS = ('related', 'corrects', 'supersedes')



def parse_record_file(path):
    match = re.search(r'<!-- research-record\s*\n(.*?)\n-->', path.read_text(encoding='utf-8'), re.S)
    if not match:
        raise ValueError('Missing research-record metadata')
    record = json.loads(match[1])
    if not isinstance(record, dict) or not isinstance(record.get('id'), str) or not record['id']:
        raise ValueError('Missing record ID')
    for field in ('title', 'summary', 'scope'):
        if not isinstance(record.get(field), str):
            raise ValueError(f'Missing/invalid {field}')
    for field in ('topics', *RELATIONS):
        values = record.get(field, [])
        if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
            raise ValueError(f'Invalid {field}')
    return dict(record, _filepath=str(path))


def event_interval(value):
    """Use the date written in the source timezone; never infer from recorded_at."""
    if value is None or value == '':
        return None
    if not isinstance(value, str):
        raise ValueError('Invalid occurred_at')
    parts = re.split(r'\s*(?:/|\.\.|~|至)\s*', value.strip())
    if len(parts) not in (1, 2):
        raise ValueError('Unsupported event date/range')
    dates = []
    for part in parts:
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', part):
            dates.append(date.fromisoformat(part))
        elif re.match(r'^\d{4}-\d{2}-\d{2}T', part):
            dates.append(datetime.fromisoformat(part.replace('UTC', '+00:00').replace('Z', '+00:00')).date())
        else:
            raise ValueError('Unsupported event date/range')
    start, end = dates[0], dates[-1]
    if start > end:
        raise ValueError('Reversed event interval')
    return start, end


def load_routes(path):
    if path is None:
        return {}
    patterns = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(patterns, dict) or any(
        not isinstance(name, str) or not name or not isinstance(pattern, str) or not pattern
        for name, pattern in patterns.items()
    ):
        raise ValueError('Routes must be a JSON object of nonempty names and regex strings')
    if set(patterns) & {'review', 'unclassified'}:
        raise ValueError('review and unclassified are reserved route names')
    for pattern in patterns.values():
        try:
            re.compile(pattern)
        except re.error as error:
            raise ValueError(f'Invalid route regex: {error}') from error
    return patterns


def classify(record, patterns):
    text = ' '.join([record['id'], record['title'], *record.get('topics', [])]).replace('_', ' ').upper()
    hits = sorted(name for name, pattern in patterns.items() if re.search(pattern, text))
    return (hits[0] if len(hits) == 1 else 'review' if hits else 'unclassified'), hits


def extract(records_dir, since, until, patterns=None):
    patterns = patterns or {}
    if since > until:
        raise ValueError('since must not be after until')
    if not records_dir.is_dir():
        raise ValueError(f'Records directory not found: {records_dir}')
    records, unknown, selected, issues = {}, [], [], []
    for path in sorted(records_dir.glob('*.md')):
        try:
            record = parse_record_file(path)
            if record['id'] in records:
                raise ValueError(f'Duplicate ID: {record["id"]}')
        except (OSError, ValueError, TypeError) as error:
            issues.append(f'{path}: {error}')
            continue
        record['_route'], record['_route_candidates'] = classify(record, patterns)
        records[record['id']] = record
        try:
            interval = event_interval(record.get('occurred_at'))
        except ValueError as error:
            issues.append(f'{path}: {error}')
            interval = None
        if interval is None:
            record['_date_status'] = 'unknown_or_invalid'
            unknown.append(record)
        else:
            start, end = interval
            record['_event_interval'] = [start.isoformat(), end.isoformat()]
            if start <= until and end >= since:
                selected.append(record)
    selected.sort(key=lambda r: (*r['_event_interval'], r['id']))
    # Traverse both directions of correction/supersession links, without declaring
    # a record obsolete or pulling the entire related-history graph into the window.
    adjacency = {key: set() for key in records}
    for record in records.values():
        for relation in RELATIONS:
            for target in record.get(relation, []):
                if target not in records:
                    issues.append(f'{record["id"]}: missing {relation} target {target}')
                elif relation != 'related':
                    adjacency[record['id']].add(target)
                    adjacency[target].add(record['id'])
    selected_ids = {r['id'] for r in selected}
    visited, pending = set(selected_ids), sorted(selected_ids)
    while pending:
        for target in sorted(adjacency[pending.pop()]):
            if target not in visited:
                visited.add(target)
                pending.append(target)
    context = [records[key] for key in sorted(visited - selected_ids)]
    edges = [dict(source=key, relation=relation, target=target)
             for key in sorted(visited) for relation in RELATIONS
             for target in records[key].get(relation, [])]
    return dict(schema_version=2, window=dict(since=str(since), until=str(until)),
                verification='metadata_only; evidence hashes and claims not verified',
                date_policy='occurred_at interval overlap; source calendar date; no recorded_at fallback',
                route_patterns=patterns, scanned=len(list(records_dir.glob('*.md'))), records=selected,
                unknown_dates=unknown, correction_context=context, relations=edges, issues=issues)


def markdown(result):
    lines = [f'# 研究记录摘要 {result["window"]["since"]} ~ {result["window"]["until"]}', '',
             '仅提取元数据，未核验来源哈希、测量或结论；分类冲突须人工判断。',
             '按来源自身日历日期及区间交集筛选；未知日期不计入本期。', '',
             f'本期 {len(result["records"])} 条；未知日期 {len(result["unknown_dates"])} 条；跨期修正背景 {len(result["correction_context"])} 条。']
    for title, rows in [('本期事件', result['records']), ('日期未知或无效（不计入本期）', result['unknown_dates']),
                        ('修正链背景（不计入本期，可能晚于本期）', result['correction_context'])]:
        lines += ['', f'## {title}', '']
        for record in rows:
            lines += [f'- {record["id"]} · {record["title"]} · {record.get("occurred_at") or "未知"} · {record["_route"]}',
                      f'  - 路径：{record["_filepath"]}', f'  - Scope：{record["scope"]}',
                      f'  - 摘要：{record["summary"]}']
            for relation in RELATIONS:
                if record.get(relation):
                    lines.append(f'  - {relation}: {", ".join(record[relation])}')
    lines += ['', '## 提取问题', ''] + (['- ' + issue for issue in result['issues']] or ['无解析或关系缺口；不代表证据已验证。'])
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--since', required=True, type=date.fromisoformat)
    parser.add_argument('--until', required=True, type=date.fromisoformat)
    parser.add_argument('--records-dir', type=Path, default=Path('docs/research/records'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--routes-file', type=Path, help='Optional JSON object mapping route names to regex patterns')
    parser.add_argument('--json', action='store_true', help='Version 2 envelope, including unknown dates and correction context')
    args = parser.parse_args()
    try:
        patterns = load_routes(args.routes_file)
        result = extract(args.records_dir, args.since, args.until, patterns)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    text = json.dumps(result, ensure_ascii=False, indent=2) + '\n' if args.json else markdown(result)
    if args.output:
        args.output.write_text(text, encoding='utf-8')
    else:
        print(text, end='')
    for issue in result['issues']:
        print(issue, file=sys.stderr)
    return 2 if result['issues'] else 0


if __name__ == '__main__':
    sys.exit(main())
