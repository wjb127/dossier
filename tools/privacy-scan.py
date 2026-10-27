#!/usr/bin/env python3
"""privacy-scan — push 전에 공개 저장소에 개인정보가 섞였는지 검사한다.

검사 대상
  1) git 이 추적하는 파일(스테이징된 파일 포함)
  2) 커밋 정보: 작성자 이름·이메일, 커밋 메시지 (--no-history 로 끌 수 있다)

검사 기준
  - 내장 규칙: 한국 휴대폰·일반 전화번호, 이메일(GitHub noreply·예시 도메인 제외),
    1Password 참조(op://), 흔한 API 키 형식
  - 금지어 목록: 한 줄에 하나. 기본 위치 ~/.config/dossier/denylist.txt (저장소 밖에 둔다)
    실제 색인에서 고객명·전화번호·도메인·폴더명을 뽑아 만든다. 이 파일은 절대 커밋하지 않는다.

출력은 "파일:줄 규칙" 만 찍는다. 금지어 자체는 출력하지 않는다(터미널 기록에도 남기지 않기 위해 번호로 표시).
발견이 하나라도 있으면 종료코드 1.

사용
  python3 tools/privacy-scan.py [--denylist 경로] [--no-history]
"""
import argparse
import os
import re
import subprocess
import sys

BUILTIN = [
    ("phone-kr-mobile", re.compile(r"(?<!\d)01[016789][-. ]?\d{3,4}[-. ]?\d{4}(?!\d)")),
    ("phone-kr-line", re.compile(r"(?<!\d)0(2|[3-6][1-5]|70)[-. ]\d{3,4}[-. ]\d{4}(?!\d)")),
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    # 아래 정규식은 문자열을 나눠 쓴다 — 붙여 쓰면 이 파일이 스스로 걸린다
    ("op-ref", re.compile(r"op:" + r"//[^\s'\"`)]+")),
    ("api-key", re.compile(r"(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|xox[bp]-[A-Za-z0-9-]{10,})")),
]
# 공개해도 되는 이메일 (예시 도메인, GitHub noreply)
EMAIL_OK = re.compile(r"@(users\.noreply\.github\.com|example\.(com|org|net)|anthropic\.com)$", re.I)


def run(*args):
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout


def load_denylist(path):
    if not os.path.exists(path):
        print(f"[경고] 금지어 목록 없음: {path} — 내장 규칙만 검사한다", file=sys.stderr)
        return []
    with open(path, encoding="utf-8") as f:
        terms = [t.strip() for t in f if t.strip() and not t.startswith("#")]
    # 길이 내림차순 + 사전순 — 실행마다 같은 번호가 나와야 "금지어 #N" 으로 추적할 수 있다
    return sorted(set(terms), key=lambda t: (-len(t), t))


def scan_text(label, text, terms, hits):
    for n, line in enumerate(text.splitlines(), 1):
        for name, rx in BUILTIN:
            for m in rx.finditer(line):
                if name == "email" and EMAIL_OK.search(m.group(0)):
                    continue
                hits.append(f"{label}:{n} 내장규칙 {name}")
        low = line.lower()
        for i, t in enumerate(terms):
            if t.lower() in low:
                hits.append(f"{label}:{n} 금지어 #{i}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--denylist", default=os.path.expanduser("~/.config/dossier/denylist.txt"))
    ap.add_argument("--no-history", action="store_true")
    a = ap.parse_args()

    root = run("git", "rev-parse", "--show-toplevel").strip()
    os.chdir(root)
    terms = load_denylist(a.denylist)
    hits = []

    files = sorted(set(run("git", "ls-files").splitlines()) | set(run("git", "diff", "--cached", "--name-only").splitlines()))
    for f in files:
        if not os.path.isfile(f):
            continue
        try:
            with open(f, encoding="utf-8") as fh:
                text = fh.read()
        except UnicodeDecodeError:
            continue  # 바이너리는 건너뛴다
        scan_text(f, text, terms, hits)
        scan_text(f"(경로) {f}", f, terms, hits)

    if not a.no_history:
        has_commit = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], capture_output=True).returncode == 0
        if has_commit:
            meta = run("git", "log", "--format=%H%n%an <%ae>%n%cn <%ce>%n%B%n---")
            scan_text("(커밋 정보)", meta, terms, hits)

    # 저장소 로컬 커밋 이메일도 확인 (다음 커밋에 들어갈 값)
    email = subprocess.run(["git", "config", "user.email"], capture_output=True, text=True).stdout.strip()
    if email and not EMAIL_OK.search(email):
        hits.append("(git config) user.email 이 공개용(noreply)이 아니다")

    if hits:
        print(f"개인정보 의심 {len(hits)}건 — push 하지 말 것")
        for h in hits:
            print("  " + h)
        sys.exit(1)
    print(f"통과: 파일 {len(files)}개, 금지어 {len(terms)}개, 커밋 정보 {'검사' if not a.no_history else '생략'}")


if __name__ == "__main__":
    main()
