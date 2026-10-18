"""DSO 429 HW3 solver: reads questions.csv, writes answers/round-XXXX.json for unanswered rounds."""
import csv, json, re, sys, os, math
from datetime import datetime, timedelta

def num(s):
    s = s.replace('$', '').replace(',', '').replace('%', '').replace('units', '').strip()
    return float(s)

def nums(text):
    return [float(x.replace(',', '')) for x in re.findall(r'-?\d[\d,]*\.?\d*', text)]

def compute(q):
    t = q['question_text']
    n = nums(t)
    if 'compounded annually' in t:
        P, r, y = n[0], n[1], n[2]
        return P * (1 + r / 100) ** y
    if 'gross margin' in t:
        return (n[0] - n[1]) / n[0] * 100
    if 'headcount series' in t:
        s = n[:5]
        d = s[1] - s[0]
        if all(abs((s[i+1]-s[i]) - d) < 1e-9 for i in range(4)):
            return s[-1] + d
        ratio = s[1] / s[0]
        return s[-1] * ratio
    if 'is discounted by' in t:
        return n[0] * (1 - n[1] / 100)
    if 'percentage change' in t:
        return (n[1] - n[0]) / n[0] * 100
    if 'settlement period' in t:
        m = re.search(r'signed on (\d+ \w+ \d{4}) has a (\d+)-day', t)
        d = datetime.strptime(m.group(1), '%d %B %Y') + timedelta(days=int(m.group(2)))
        return f"{d.day} {d.strftime('%B %Y')}"
    if 'break even' in t:
        return n[0] / (n[1] - n[2])
    if 'probability' in t:
        return n[0] / (n[0] + n[1] + n[2]) * 100
    if 'overall average' in t:
        return (n[0] * n[1] + n[2] * n[3]) / (n[0] + n[2])
    if 'converted to euros' in t:
        return n[0] * n[1]
    if 'total revenue' in t:
        return n[0] * n[1]
    if 'split between two channels' in t:
        return n[0] * n[1] / (n[1] + n[2])
    return None

def choose(q):
    opts = [q['option_a'], q['option_b'], q['option_c'], q['option_d']]
    v = compute(q)
    if v is None:
        return None
    if isinstance(v, str):
        for L, o in zip('ABCD', opts):
            if o.strip() == v:
                return L
        return None
    if 'break even' in q['question_text']:
        targets = [round(v), math.ceil(v)]
    else:
        targets = [v]
    best = min(zip('ABCD', opts), key=lambda p: min(abs(num(p[1]) - x) for x in targets))
    return best[0]

def main(qfile, outdir, rounds=None):
    rows = list(csv.DictReader(open(qfile, newline='', encoding='utf-8')))
    by_round = {}
    for r in rows:
        by_round.setdefault(int(r['round_id']), []).append(r)
    os.makedirs(outdir, exist_ok=True)
    unknown = []
    for rid in sorted(by_round):
        if rounds and rid not in rounds:
            continue
        path = os.path.join(outdir, f'round-{rid:04d}.json')
        if os.path.exists(path):
            continue
        ans = {}
        for q in sorted(by_round[rid], key=lambda x: int(x['q_index'])):
            a = choose(q)
            if a is None:
                unknown.append((rid, q['q_index'], q['question_text']))
                a = 'A'
            ans[f"q{int(q['q_index'])}"] = a
        if len(ans) == 25:
            json.dump({'round_id': rid, 'answers': ans}, open(path, 'w'), indent=2)
            print('wrote', path)
    for u in unknown:
        print('UNKNOWN TYPE:', u, file=sys.stderr)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
