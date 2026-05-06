#!/usr/bin/env bash
# publish_draft.sh — manually publish a saved TokyLabs blog draft to Selldone.
# Usage: SELLDONE_TOKEN=<token> bash publish_draft.sh [YYYY-MM-DD]
# If no date is given, today's date is used.
set -euo pipefail

DATE="${1:-$(date +%Y-%m-%d)}"
DRAFT="$HOME/Documents/tokylabs-drafts/${DATE}.md"
LOG="$HOME/Documents/tokylabs-blog-log.txt"
SHOP_ID="2362"
API_URL="https://api.selldone.com/shops/${SHOP_ID}/blogs"

if [[ -z "${SELLDONE_TOKEN:-}" ]]; then
  echo "ERROR: SELLDONE_TOKEN environment variable is not set." >&2
  exit 1
fi

if [[ ! -f "$DRAFT" ]]; then
  echo "ERROR: Draft not found at $DRAFT" >&2
  exit 1
fi

# Extract title (first # heading) and body (everything after the first blank line past the heading)
TITLE=$(grep -m1 '^# ' "$DRAFT" | sed 's/^# //')
# Body: strip the first two comment blocks and the title line, keep the HTML
BODY=$(awk '/^<p>/{found=1} found{print}' "$DRAFT" | tr '\n' ' ')

echo "Publishing: $TITLE"
echo "Endpoint:   $API_URL"

RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "$API_URL" \
  -H "Authorization: Bearer $SELLDONE_TOKEN" \
  -H "Content-Type: application/json" \
  --data "$(jq -n --arg title "$TITLE" --arg body "$BODY" '{"title":$title,"body":$body,"published":true}')")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY_RESP=$(echo "$RESPONSE" | head -n-1)

if [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "201" ]]; then
  BLOG_ID=$(echo "$BODY_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id','unknown'))" 2>/dev/null || echo "unknown")
  echo "SUCCESS — Blog ID: $BLOG_ID"
  # Update log: replace FAILED line with Published line
  sed -i "s|Status: FAILED.*|Status: Published ✅  |  Blog ID: $BLOG_ID|" "$LOG"
  echo "[$DATE] Status updated to Published in log." | tee -a "$LOG"
else
  echo "FAILED — HTTP $HTTP_CODE"
  echo "$BODY_RESP"
  exit 1
fi
