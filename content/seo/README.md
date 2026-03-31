# FirmFlow SEO Content Seeds

This directory holds the structured data that drives the Phase 1 static pSEO/AEO generator.

## Files

- `site.json`: site-wide defaults such as the base URL, organization metadata, disclaimer text, and existing core pages for the sitemap.
- `counties.json`: county-level workflow content seeds.
- `forms.json`: form-level workflow content seeds.
- `workflows.json`: broader workflow explainers.
- `pages.json`: the explicit list of pages to generate.

## Generate the pages

Run:

```bash
python3 scripts/generate_seo.py
```

This rewrites:

- generated SEO pages under `counties/`, `forms/`, and `workflows/`
- `sitemap.xml`
- `robots.txt`

## Add a new county page

1. Add a county object to `counties.json`.
2. Add a page seed with `"page_type": "county"` to `pages.json`.
3. Re-run `python3 scripts/generate_seo.py`.

## Add a new form page

1. Add a form object to `forms.json`.
2. Add a page seed with `"page_type": "form"` to `pages.json`.
3. Re-run `python3 scripts/generate_seo.py`.

## Add a new county + form page

1. Make sure the county exists in `counties.json`.
2. Make sure the form exists in `forms.json`.
3. Add a page seed with `"page_type": "county_form"` plus `county_id` and `form_id` to `pages.json`.
4. Re-run `python3 scripts/generate_seo.py`.

## Add a new workflow page

1. Add a workflow object to `workflows.json`.
2. Add a page seed with `"page_type": "workflow"` to `pages.json`.
3. Re-run `python3 scripts/generate_seo.py`.

## Content guardrails

- Use cautious, educational wording.
- Do not treat county workflows as fixed procedural rules.
- Do not publish legal advice.
- When county-specific requirements could vary, say so directly and remind firms to verify current court and local filing requirements.
