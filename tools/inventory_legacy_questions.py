from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any
try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None
CANDIDATE_EXT = {'.json', '.yaml', '.yml', '.typ', '.md', '.gift'}
NAME_RX = re.compile(r'(quiz|question|bank|assessment|exam|test)', re.I)
EXCLUDE_RX = re.compile(r'(^|/)(Markdown|MarkdownPreview|reference|build|bin|obj)(/|$)', re.I)
def run_git(*args: str) -> str:
    return subprocess.check_output(['git', *args], text=True, errors='replace')
def normalized_stem(value: str) -> str:
    value = re.sub(r'[`*_#>]+', ' ', value)
    value = re.sub(r'\s+', ' ', value).strip().lower()
    return value
def signature_for(stem: str) -> str:
    value = normalized_stem(stem)
    return hashlib.sha256(value.encode()).hexdigest()[:20] if value else ''
def strip_typst_line_comments(text: str) -> str:
    return '\n'.join(re.sub(r'^(\s*)//\s?', r'\1', line) for line in text.splitlines())
def decode_quoted(value: str) -> str:
    try:
        return bytes(value, 'utf-8').decode('unicode_escape')
    except Exception:
        return value
def quoted_strings(value: str) -> list[str]:
    return [decode_quoted(v) for v in re.findall(r'"((?:\\.|[^"\\])*)"', value, re.S)]
def branch_names() -> list[str]:
    refs = run_git('for-each-ref', '--format=%(refname:short)', 'refs/remotes/origin').splitlines()
    return sorted({ref.removeprefix('origin/') for ref in refs if ref.startswith('origin/') and ref != 'origin/HEAD'})
def show(branch: str, path: str) -> str:
    return subprocess.check_output(['git', 'show', f'origin/{branch}:{path}'], text=True, errors='replace')
def add_record(records: list[dict[str, Any]], branch: str, path: str, source_kind: str, raw: dict[str, Any], ordinal: int | None = None) -> None:
    stem = str(raw.get('stem') or raw.get('text') or raw.get('question') or '').strip()
    records.append({'branch': branch,'path': path,'source_kind': source_kind,'ordinal': ordinal,'source_id': str(raw.get('id') or raw.get('key') or ''),'type': raw.get('type'),'stem': stem,'signature': signature_for(stem),'raw': raw})
def parse_json(branch: str, path: str, text: str, records: list[dict[str, Any]]) -> None:
    try:
        data = json.loads(text)
    except Exception:
        return
    if isinstance(data, dict) and isinstance(data.get('questions'), list):
        for i, item in enumerate(data['questions'], 1):
            if isinstance(item, dict): add_record(records, branch, path, 'json-bank', item, i)
    elif isinstance(data, dict) and data.get('stem') and data.get('type'):
        add_record(records, branch, path, 'json-item', data, 1)
def parse_yaml(branch: str, path: str, text: str, records: list[dict[str, Any]]) -> None:
    if yaml is None: return
    try:
        data = yaml.safe_load(text)
    except Exception:
        return
    if isinstance(data, dict) and data.get('stem') and data.get('type'):
        add_record(records, branch, path, 'yaml-item', data, 1)
    elif isinstance(data, list):
        for i, item in enumerate(data, 1):
            if isinstance(item, dict) and (item.get('stem') or item.get('text')): add_record(records, branch, path, 'yaml-list', item, i)
def split_typst_entries(text: str):
    starts = list(re.finditer(r'^\s*"([A-Za-z0-9_.-]+)"\s*:\s*\(', text, re.M))
    for idx, match in enumerate(starts):
        end = starts[idx + 1].start() if idx + 1 < len(starts) else len(text)
        yield match.group(1), text[match.start():end]
def typst_field(block: str, field: str) -> str | None:
    match = re.search(rf'\b{re.escape(field)}\s*:\s*"((?:\\.|[^"\\])*)"', block, re.S)
    return decode_quoted(match.group(1)) if match else None
def parse_typst_tuple_bank(branch: str, path: str, text: str, records: list[dict[str, Any]]) -> None:
    name = Path(path).name.lower()
    if not (name.endswith('_bank.typ') or '/banks/' in path.lower()): return
    qtype = None
    if name.startswith('mc_') or name == 'mc_bank.typ': qtype = 'mcq_one'
    elif name.startswith('tf_') or name == 'tf_bank.typ': qtype = 'true_false'
    elif name.startswith('sa_') or name == 'sa_bank.typ': qtype = 'short_answer'
    elif name.startswith('fib_') or name == 'fib_bank.typ': qtype = 'fill_blank'
    elif name.startswith('cr_') or name == 'cr_bank.typ': qtype = 'code_review'
    for i, (key, block) in enumerate(split_typst_entries(text), 1):
        stem = typst_field(block, 'text') or typst_field(block, 'stem') or typst_field(block, 'question') or ''
        if not stem: continue
        raw: dict[str, Any] = {'id': key, 'type': qtype, 'stem': stem}
        correct = re.search(r'\bcorrect\s*:\s*([0-9]+|true|false)', block, re.I)
        if correct:
            token = correct.group(1).lower(); raw['legacy_correct'] = int(token) if token.isdigit() else token == 'true'
        answer = typst_field(block, 'answer')
        if answer is not None: raw['legacy_answer'] = answer
        choices = re.search(r'\bchoices\s*:\s*\((.*?)\)\s*,?\s*(?:correct|answer|solution|$)', block, re.S)
        if choices: raw['legacy_choices'] = quoted_strings(choices.group(1))
        add_record(records, branch, path, 'typst-bank', raw, i)
def parse_typst_calls(branch: str, path: str, text: str, records: list[dict[str, Any]]) -> None:
    scan = strip_typst_line_comments(text)
    existing = {(r['source_kind'], r['signature']) for r in records if r['branch'] == branch and r['path'] == path}
    mc_rx = re.compile(r'#mc\s*\(\s*"((?:\\.|[^"\\])*)"\s*,\s*\((.*?)\)\s*,\s*correct\s*:\s*(\d+)\s*\)', re.S)
    for i, m in enumerate(mc_rx.finditer(scan), 1):
        stem = decode_quoted(m.group(1)); choices = quoted_strings(m.group(2)); correct = int(m.group(3)); sig = signature_for(stem)
        if ('typst-bank', sig) in existing: continue
        add_record(records, branch, path, 'typst-mc-call', {'type':'mcq_one','stem':stem,'legacy_choices':choices,'legacy_correct':correct}, i)
    tf_rx = re.compile(r'#tf\s*\(\s*"((?:\\.|[^"\\])*)"\s*,\s*(true|false)\s*\)', re.I | re.S)
    for i, m in enumerate(tf_rx.finditer(scan), 1):
        stem = decode_quoted(m.group(1)); sig = signature_for(stem)
        if ('typst-bank', sig) in existing: continue
        add_record(records, branch, path, 'typst-tf-call', {'type':'true_false','stem':stem,'answer':m.group(2).lower() == 'true'}, i)
    numbered = list(re.finditer(r'(?m)^\s*(\d+)\.\s+([^\n]+(?:\? |\?|:)?)[ \t]*$', scan))
    for idx, m in enumerate(numbered):
        stem = m.group(2).strip()
        if len(stem) < 8 or not ('?' in stem or Path(path).name.lower().startswith('sa')): continue
        end = numbered[idx + 1].start() if idx + 1 < len(numbered) else min(len(scan), m.end() + 2000)
        chunk = scan[m.end():end]
        ans = re.search(r'Answer:\]\s*\n\s*"((?:\\.|[^"\\])*)"', chunk, re.S)
        raw = {'type':'short_answer','stem':stem}
        if ans: raw['legacy_answer'] = decode_quoted(ans.group(1))
        add_record(records, branch, path, 'typst-numbered-sa', raw, int(m.group(1)))
    if NAME_RX.search(path) and not any(r['branch'] == branch and r['path'] == path for r in records):
        for line in scan.splitlines():
            s = line.strip()
            if s.startswith('#') or not s.endswith('?') or len(s) < 12: continue
            add_record(records, branch, path, 'typst-bare-question', {'type':'essay','stem':s}, None)
def section_before(text: str, pos: int) -> str:
    headings = list(re.finditer(r'(?m)^#{1,6}\s+(.+)$', text[:pos])); return headings[-1].group(1).strip() if headings else ''
def difficulty_before(text: str, pos: int) -> str | None:
    matches = list(re.finditer(r'(?im)^#{1,6}\s+.*\b(Easy|Medium|Hard)\b.*$', text[:pos])); return matches[-1].group(1).lower() if matches else None
def parse_markdown(branch: str, path: str, text: str, records: list[dict[str, Any]]) -> None:
    qrx = re.compile(r'(?m)^\s*(?:\*\*)?Q(\d+)\.(?:\*\*)?\s*(.+?)\s*$'); matches = list(qrx.finditer(text))
    for idx, m in enumerate(matches):
        stem = re.sub(r'\s{2,}$', '', m.group(2)).strip()
        if not stem: continue
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text); chunk = text[m.end():end]; section = section_before(text, m.start()).lower(); diff = difficulty_before(text, m.start()); raw: dict[str, Any] = {'stem':stem}
        if diff: raw['difficulty'] = diff
        choices = [(cm.group(1), cm.group(2).strip()) for cm in re.finditer(r'(?m)^\s*([A-J])\.\s+(.+?)\s*$', chunk)]
        answer = re.search(r'(?im)^\s*\*\*Answer:?\*\*\s*:?\s*([^\n]+)|^\s*\*\*Answer:\s*([^*\n]+)\*\*', chunk)
        if 'multiple choice' in section or choices:
            raw['type'] = 'mcq_one'; raw['legacy_choices'] = [v for _, v in choices]
            if answer:
                token = (answer.group(1) or answer.group(2) or '').strip().strip('*')
                if re.fullmatch(r'[A-J]', token, re.I): raw['legacy_correct'] = ord(token.upper()) - ord('A')
                else: raw['legacy_answer'] = token
        elif 'true/false' in section or 'true false' in section:
            raw['type'] = 'true_false'; inline = re.search(r'\((True|False)(?:\s*[-–].*)?\)\s*$', stem, re.I)
            if inline: raw['answer'] = inline.group(1).lower() == 'true'; raw['stem'] = stem[:inline.start()].rstrip()
            elif answer:
                token = (answer.group(1) or answer.group(2) or '').strip()
                if token.lower().startswith(('true','false')): raw['answer'] = token.lower().startswith('true')
        else:
            raw['type'] = 'short_answer'
            if answer: raw['legacy_answer'] = (answer.group(1) or answer.group(2) or '').strip().strip('*')
        add_record(records, branch, path, 'markdown-q', raw, int(m.group(1)))
    if NAME_RX.search(path):
        nrx = re.compile(r'(?m)^\s*(\d+)\.\s+(.+?\?)\s*$'); existing_sigs = {r['signature'] for r in records if r['branch'] == branch and r['path'] == path}
        for m in nrx.finditer(text):
            stem = m.group(2).strip(); sig = signature_for(stem)
            if sig in existing_sigs: continue
            add_record(records, branch, path, 'markdown-numbered', {'type':'short_answer','stem':stem}, int(m.group(1))); existing_sigs.add(sig)
    set_rx = re.compile(r'(?ms)^\*\*Set\s+([^*]+)\*\*\s*\n(.*?)(?=^\*\*Set\s+|^---\s*$|\Z)')
    for i, m in enumerate(set_rx.finditer(text), 1):
        block = m.group(2); a = re.search(r'\*\*Column A:\*\*\s*(.*?)(?=\*\*Column B:\*\*)', block, re.S); b = re.search(r'\*\*Column B:\*\*\s*(.*?)(?=\*\*Answers:\*\*)', block, re.S); ans = re.search(r'\*\*Answers:\*\*\s*([^\n]+)', block)
        if not (a and b and ans): continue
        left = {x.group(1): x.group(2).strip() for x in re.finditer(r'(?m)^([A-Z])\.\s+(.+)$', a.group(1))}; right = {x.group(1): x.group(2).strip() for x in re.finditer(r'(?m)^(\d+)\.\s+(.+)$', b.group(1))}; pairs=[]
        for lm, rm in re.findall(r'([A-Z])-(\d+)', ans.group(1)):
            if lm in left and rm in right: pairs.append({'source':left[lm],'target':right[rm]})
        if len(pairs) >= 2: add_record(records, branch, path, 'markdown-matching', {'type':'matching','stem':f'Match the items for {m.group(1).strip()}.','pairs':pairs}, i)
    hrx = re.compile(r'(?im)^###\s+(?:Question\s+)?(\d+)[^\n]*\n+(.+)$'); existing_sigs = {r['signature'] for r in records if r['branch'] == branch and r['path'] == path}
    for m in hrx.finditer(text):
        stem = m.group(2).strip()
        if len(stem) < 8 or signature_for(stem) in existing_sigs: continue
        add_record(records, branch, path, 'markdown-heading', {'type':'short_answer','stem':stem}, int(m.group(1))); existing_sigs.add(signature_for(stem))
def parse_gift(branch: str, path: str, text: str, records: list[dict[str, Any]]) -> None:
    rx = re.compile(r'(?ms)::([^:]+)::\s*(.*?)\s*\{(.*?)\}')
    for i, m in enumerate(rx.finditer(text), 1):
        name, stem, body = m.group(1).strip(), m.group(2).strip(), m.group(3).strip(); raw: dict[str, Any] = {'id':name,'stem':stem}
        if body.upper() in {'T','TRUE','F','FALSE'}: raw['type']='true_false'; raw['answer']=body.upper().startswith('T')
        else:
            options=[]; correct_index=None
            for om in re.finditer(r'([=~])([^=~#\n}]+)', body):
                options.append(om.group(2).strip())
                if om.group(1)=='=' and correct_index is None: correct_index=len(options)-1
            if options and correct_index is not None: raw['type']='mcq_one'; raw['legacy_choices']=options; raw['legacy_correct']=correct_index
            else: raw['type']='short_answer'; raw['legacy_answer']=body
        add_record(records, branch, path, 'gift', raw, i)
def scan_repo(output: Path) -> dict[str, Any]:
    branches = branch_names(); candidate_files=[]; by_blob=defaultdict(list); records=[]
    for branch in branches:
        for path in run_git('ls-tree','-r','--name-only',f'origin/{branch}').splitlines():
            p=Path(path)
            if p.suffix.lower() not in CANDIDATE_EXT or EXCLUDE_RX.search(path): continue
            if not NAME_RX.search(path) and p.suffix.lower() != '.gift': continue
            try: blob=run_git('rev-parse',f'origin/{branch}:{path}').strip(); text=show(branch,path)
            except Exception: continue
            candidate_files.append({'branch':branch,'path':path,'blob':blob,'sha256':hashlib.sha256(text.encode()).hexdigest(),'bytes':len(text.encode()),'lines':text.count('\n')+1}); by_blob[blob].append({'branch':branch,'path':path}); ext=p.suffix.lower()
            if ext=='.json': parse_json(branch,path,text,records)
            elif ext in {'.yaml','.yml'}: parse_yaml(branch,path,text,records)
            elif ext=='.typ': parse_typst_tuple_bank(branch,path,text,records); parse_typst_calls(branch,path,text,records)
            elif ext=='.md': parse_markdown(branch,path,text,records)
            elif ext=='.gift': parse_gift(branch,path,text,records)
    groups=defaultdict(list)
    for rec in records:
        if rec['signature']: groups[rec['signature']].append({k:rec[k] for k in ('branch','path','source_id','source_kind','type','stem')})
    manifest={'branches':branches,'candidate_files':candidate_files,'identical_file_groups':[v for v in by_blob.values() if len(v)>1],'extracted_items':records,'duplicate_stem_groups':[v for v in groups.values() if len(v)>1]}; output.mkdir(parents=True,exist_ok=True); (output/'source-inventory.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    branch_counts=defaultdict(int); kind_counts=defaultdict(int)
    for rec in records: branch_counts[rec['branch']]+=1; kind_counts[rec['source_kind']]+=1
    lines=['# Question Source Migration Inventory','', '> Generated by Quizbank legacy-source inventory. This report is not the canonical bank.','',f'**Branches scanned:** {len(branches)}  ',f'**Candidate source files:** {len(candidate_files)}  ',f'**Extracted question occurrences:** {len(records)}  ',f'**Unique normalized stems:** {len(groups)}  ',f'**Duplicate-stem groups:** {sum(len(v)>1 for v in groups.values())}','','## Branches',''] + [f'- `{b}`: {branch_counts[b]} extracted occurrences' for b in branches] + ['', '## Source kinds',''] + [f'- `{k}`: {v}' for k,v in sorted(kind_counts.items())] + ['', '## Candidate files','','| Branch | Path | Lines | SHA-256 |','|---|---|---:|---|']
    for rec in sorted(candidate_files,key=lambda r:(r['branch'],r['path'])): lines.append(f"| `{rec['branch']}` | `{rec['path']}` | {rec['lines']} | `{rec['sha256'][:12]}` |")
    (output/'source-inventory.md').write_text('\n'.join(lines).rstrip()+'\n'); return manifest
def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument('--output',default='F26/QuizBanks/migration'); args=parser.parse_args(); manifest=scan_repo(Path(args.output)); print(f"branches={len(manifest['branches'])} files={len(manifest['candidate_files'])} occurrences={len(manifest['extracted_items'])}"); return 0
if __name__=='__main__': raise SystemExit(main())
