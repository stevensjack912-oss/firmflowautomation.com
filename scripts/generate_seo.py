#!/usr/bin/env python3
"""Generate Phase 1 pSEO/AEO pages for the static FirmFlow site."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from string import Template
from typing import Dict, List


ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content" / "seo"
TEMPLATE_DIR = ROOT / "templates" / "seo"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_template(relative_path: str) -> Template:
    return Template((TEMPLATE_DIR / relative_path).read_text(encoding="utf-8"))


def rel_prefix(depth: int) -> str:
    return "../" * depth


def asset_path(root_path: str, name: str) -> str:
    return f"{root_path}{name}"


def to_html_list(items: List[str]) -> str:
    return "".join(f"<li>{escape(item)}</li>" for item in items)


def render_faq_items(items: List[Dict[str, str]]) -> str:
    blocks = []
    for item in items:
        q = escape(item["question"])
        a = escape(item["answer"])
        blocks.append(
            "<div class=\"faq-item\">"
            "<button class=\"faq-question\" aria-expanded=\"false\">"
            f"{q}"
            "<svg class=\"faq-chevron\" viewBox=\"0 0 24 24\" aria-hidden=\"true\">"
            "<polyline points=\"6 9 12 15 18 9\"></polyline>"
            "</svg>"
            "</button>"
            "<div class=\"faq-answer\" role=\"region\">"
            f"<div class=\"faq-answer-inner\">{a}</div>"
            "</div>"
            "</div>"
        )
    return "".join(blocks)


def render_breadcrumbs(crumbs: List[Dict[str, str]]) -> str:
    items = []
    for idx, crumb in enumerate(crumbs):
        label = escape(crumb["label"])
        if idx == len(crumbs) - 1:
            items.append(
                f"<li aria-current=\"page\"><span>{label}</span></li>"
            )
        else:
            href = escape(crumb["href"], quote=True)
            items.append(
                f"<li><a href=\"{href}\">{label}</a></li>"
            )
    return load_template("partials/breadcrumbs.html").substitute(
        breadcrumb_items="".join(items)
    )


def render_related_items(links: List[Dict[str, str]]) -> str:
    cards = []
    for link in links:
        title = escape(link["title"])
        body = escape(link["body"])
        href = escape(link["href"], quote=True)
        cards.append(
            "<article class=\"card seo-related-card\">"
            f"<h3><a href=\"{href}\">{title}</a></h3>"
            f"<p>{body}</p>"
            "</article>"
        )
    return "".join(cards)


def build_schema(context: Dict[str, object]) -> str:
    schema = [
        {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": context["meta_title"],
            "description": context["meta_description"],
            "url": context["canonical_url"],
            "isPartOf": {
                "@type": "WebSite",
                "name": context["site_name"],
                "url": context["base_url"]
            },
            "about": context["about"]
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": idx + 1,
                    "name": crumb["label"],
                    "item": crumb["absolute_url"]
                }
                for idx, crumb in enumerate(context["breadcrumbs_data"])
            ]
        }
    ]
    if context["faq_items"]:
        schema.append(
            {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": item["question"],
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": item["answer"]
                        }
                    }
                    for item in context["faq_items"]
                ]
            }
        )
    return json.dumps(schema, indent=2)


def page_depth(slug: str) -> int:
    return len(Path(slug).parts)


def absolute_url(base_url: str, path: str) -> str:
    return f"{base_url}{path}"


def build_page_context(
    site: Dict[str, object],
    counties: Dict[str, Dict[str, object]],
    forms: Dict[str, Dict[str, object]],
    workflows: Dict[str, Dict[str, object]],
    page: Dict[str, object]
) -> Dict[str, object]:
    depth = page_depth(page["slug"])
    root_path = rel_prefix(depth)
    page_type = page["page_type"]

    context: Dict[str, object] = {
        "site_name": site["site_name"],
        "base_url": site["base_url"],
        "root_path": root_path,
        "css_path": asset_path(root_path, "styles.css?v=20260330-1"),
        "js_path": asset_path(root_path, "main.js"),
        "favicon_ico": asset_path(root_path, "favicon.ico?v=20260328-2"),
        "favicon_32": asset_path(root_path, "favicon-32x32.png?v=20260328-2"),
        "favicon_16": asset_path(root_path, "favicon-16x16.png?v=20260328-2"),
        "apple_icon": asset_path(root_path, "apple-touch-icon.png?v=20260328-2"),
        "manifest_path": asset_path(root_path, "site.webmanifest?v=20260328-2"),
        "logo_path": asset_path(root_path, "assets/brand/firmflow-logo-v2.png?v=20260329-1"),
        "canonical_url": absolute_url(site["base_url"], page["canonical_slug"]),
        "disclaimer": site["default_disclaimer"],
    }

    if page_type == "county":
        county = counties[page["county_id"]]
        context.update(
            {
                "meta_title": page["meta_title"],
                "meta_description": page["meta_description"],
                "h1": page["h1"],
                "hero_label": "County Guide",
                "hero_aria": f"{county['county']} guide",
                "hero_intro": county["intro_summary"],
                "short_answer": (
                    f"{county['county']} parentage order preparation often involves statewide forms, "
                    "supporting local documents, and a careful packet review process. Exact filing requirements may vary by county, "
                    "so firms should verify current court and local filing requirements before filing."
                ),
                "workflow_context": county["workflow_context"],
                "intro_summary": county["intro_summary"],
                "county_heading": f"{county['county']} workflow context",
                "county_overview": county["workflow_context"],
                "county_notes": to_html_list(county["county_notes"]),
                "faq_items": county["faq_items"],
                "faq_heading": f"{county['county']} workflow FAQ",
                "faq_intro": "These answers are designed to help legal teams understand workflow context without making unverified procedural claims.",
                "related_heading": "Related county workflow resources",
                "related_intro": "Use these supporting pages to move from county-level workflow context into specific forms and broader parentage order planning.",
                "about": [county["county"], "California parentage order workflow"]
            }
        )
        related_links = [
            {
                "title": "FL-235 in California Parentage Order Workflows",
                "href": f"{root_path}forms/fl-235/",
                "body": "A form-focused overview of how legal teams may review FL-235 as part of broader packet preparation."
            },
            {
                "title": "California Parentage Order Workflow",
                "href": f"{root_path}workflows/california-parentage-order-workflow/",
                "body": "A workflow explainer focused on intake, form selection, packet assembly, and final review."
            }
        ]
        breadcrumbs = [
            {"label": "Home", "href": f"{root_path}index.html", "absolute_url": site["base_url"] + "/index.html"},
            {"label": "Counties", "href": f"{root_path}product.html", "absolute_url": site["base_url"] + "/product.html"},
            {"label": county["county"], "href": "", "absolute_url": context["canonical_url"]}
        ]
        template_name = "county.html"
    elif page_type == "form":
        form = forms[page["form_id"]]
        context.update(
            {
                "meta_title": page["meta_title"],
                "meta_description": page["meta_description"],
                "h1": page["h1"],
                "hero_label": "Form Guide",
                "hero_aria": f"{form['form_number']} guide",
                "hero_intro": form["intro_summary"],
                "short_answer": form["short_answer"],
                "workflow_context": form["workflow_context"],
                "intro_summary": form["intro_summary"],
                "form_heading": f"How legal teams commonly think about {form['form_number']}",
                "form_overview": form["workflow_context"],
                "county_notes": to_html_list(form["county_notes"]),
                "faq_items": form["faq_items"],
                "faq_heading": f"{form['form_number']} FAQ",
                "faq_intro": "These answers are written for workflow education and should not be treated as definitive filing instructions.",
                "related_heading": "Related form and workflow resources",
                "related_intro": "Explore the surrounding workflow context and county pages that relate to this form.",
                "about": [form["form_number"], "California surrogacy filing workflow"]
            }
        )
        related_links = [
            {
                "title": "Orange County Parentage Order Workflow Guide",
                "href": f"{root_path}counties/orange-county/",
                "body": "A county-focused guide for legal teams managing parentage order packet preparation in Orange County."
            },
            {
                "title": "California Parentage Order Workflow",
                "href": f"{root_path}workflows/california-parentage-order-workflow/",
                "body": "A workflow-level view of how firms commonly structure intake, form prep, and packet review."
            }
        ]
        breadcrumbs = [
            {"label": "Home", "href": f"{root_path}index.html", "absolute_url": site["base_url"] + "/index.html"},
            {"label": "Forms", "href": f"{root_path}product.html", "absolute_url": site["base_url"] + "/product.html"},
            {"label": form["form_number"], "href": "", "absolute_url": context["canonical_url"]}
        ]
        template_name = "form.html"
    elif page_type == "workflow":
        workflow = workflows[page["workflow_id"]]
        context.update(
            {
                "meta_title": workflow["meta_title"],
                "meta_description": workflow["meta_description"],
                "h1": workflow["h1"],
                "hero_label": "Workflow Guide",
                "hero_aria": "workflow guide",
                "hero_intro": workflow["intro_summary"],
                "short_answer": workflow["short_answer"],
                "workflow_context": workflow["workflow_context"],
                "intro_summary": workflow["intro_summary"],
                "workflow_heading": "A practical workflow view",
                "workflow_overview": workflow["workflow_context"],
                "county_notes": to_html_list(workflow["county_notes"]),
                "faq_items": workflow["faq_items"],
                "faq_heading": "Workflow FAQ",
                "faq_intro": "These answers are designed to make the workflow easy to understand and quote cleanly while staying cautious about local variation.",
                "related_heading": "Related workflow resources",
                "related_intro": "Use these links to move from broad workflow education into county-specific and form-specific context.",
                "about": ["California parentage order workflow", "Surrogacy law firm automation"]
            }
        )
        related_links = [
            {
                "title": "Orange County Parentage Order Workflow Guide",
                "href": f"{root_path}counties/orange-county/",
                "body": "A county-level guide focused on one of the current venues supported by FirmFlow PBO."
            },
            {
                "title": "Los Angeles County FL-200 Workflow Guide",
                "href": f"{root_path}counties/los-angeles-county/fl-200/",
                "body": "A high-intent county-plus-form page showing how one form may fit into a Los Angeles County workflow."
            }
        ]
        breadcrumbs = [
            {"label": "Home", "href": f"{root_path}index.html", "absolute_url": site["base_url"] + "/index.html"},
            {"label": "Workflows", "href": f"{root_path}product.html", "absolute_url": site["base_url"] + "/product.html"},
            {"label": workflow["h1"], "href": "", "absolute_url": context["canonical_url"]}
        ]
        template_name = "workflow.html"
    else:
        county = counties[page["county_id"]]
        form = forms[page["form_id"]]
        faq_items = county["faq_items"] + form["faq_items"][:1]
        context.update(
            {
                "meta_title": page["meta_title"],
                "meta_description": page["meta_description"],
                "h1": page["h1"],
                "hero_label": "County + Form Guide",
                "hero_aria": f"{county['county']} {form['form_number']} guide",
                "hero_intro": (
                    f"{form['form_number']} is commonly reviewed as part of broader California parentage workflows, "
                    f"and legal teams working in {county['county']} often want a cleaner way to understand where it may fit in the packet."
                ),
                "short_answer": (
                    f"In {county['county']}, {form['form_number']} may be reviewed as part of a broader parentage order packet. "
                    "The exact filing set may vary by county practice and by matter, so firms should verify current requirements before filing."
                ),
                "workflow_context": (
                    f"A county-aware workflow helps teams understand how {form['form_number']} may relate to the rest of a {county['county']} filing packet, "
                    "while still leaving room for matter-specific attorney review."
                ),
                "intro_summary": (
                    f"This page combines form-level and county-level workflow context for {form['form_number']} in {county['county']}. "
                    "It is intended to support packet planning and internal consistency, not to provide definitive filing instructions."
                ),
                "county_form_heading": f"{form['form_number']} within a {county['county']} workflow",
                "county_form_overview": (
                    f"Legal teams often review {form['form_number']} together with related statewide forms and county-specific materials when preparing a {county['county']} parentage order packet."
                ),
                "county_notes": to_html_list(
                    county["county_notes"] + form["county_notes"]
                ),
                "faq_items": faq_items,
                "faq_heading": f"{county['county']} + {form['form_number']} FAQ",
                "faq_intro": "These answers are intentionally cautious and workflow-focused so they can support planning without overstating local procedural rules.",
                "related_heading": "Related county and form resources",
                "related_intro": "Move from this narrow page into the broader county and workflow views that surround it.",
                "about": [county["county"], form["form_number"], "California parentage order workflow"]
            }
        )
        related_links = [
            {
                "title": "Orange County Parentage Order Workflow Guide",
                "href": f"{root_path}counties/orange-county/",
                "body": "Compare this county-plus-form page with a county-level workflow guide for another supported venue."
            },
            {
                "title": "FL-235 in California Parentage Order Workflows",
                "href": f"{root_path}forms/fl-235/",
                "body": "See how another form-focused page handles workflow context and related review steps."
            }
        ]
        breadcrumbs = [
            {"label": "Home", "href": f"{root_path}index.html", "absolute_url": site["base_url"] + "/index.html"},
            {"label": "Counties", "href": f"{root_path}product.html", "absolute_url": site["base_url"] + "/product.html"},
            {"label": county["county"], "href": f"{root_path}counties/{county['county_slug']}/", "absolute_url": site["base_url"] + f"/counties/{county['county_slug']}/"},
            {"label": form["form_number"], "href": "", "absolute_url": context["canonical_url"]}
        ]
        template_name = "county_form.html"

    context["related_links"] = load_template("partials/related_links.html").substitute(
        related_heading=context["related_heading"],
        related_intro=context["related_intro"],
        related_items=render_related_items(related_links)
    )
    context["summary_block"] = load_template("partials/summary_block.html").substitute(
        short_answer=context["short_answer"],
        workflow_context=context["workflow_context"]
    )
    context["faq_section"] = load_template("partials/faq_section.html").substitute(
        faq_heading=context["faq_heading"],
        faq_intro=context["faq_intro"],
        faq_items=render_faq_items(context["faq_items"])
    )
    context["disclaimer"] = load_template("partials/disclaimer.html").substitute(
        disclaimer=context["disclaimer"]
    )
    context["breadcrumbs"] = render_breadcrumbs(breadcrumbs)
    context["breadcrumbs_data"] = breadcrumbs
    context["template_name"] = template_name
    context["body_content"] = load_template(template_name).substitute(context)
    context["head_meta"] = load_template("partials/head_meta.html").substitute(
        meta_title=context["meta_title"],
        meta_description=context["meta_description"],
        canonical_url=context["canonical_url"],
        site_name=site["site_name"],
        og_image=site["organization"]["logo"]
    )
    context["schema_json"] = build_schema(context)
    return context


def write_page(context: Dict[str, object], slug: str):
    output_path = ROOT / slug / "index.html"
    html = load_template("base.html").substitute(context)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html + "\n", encoding="utf-8")
    return output_path


def write_sitemap(site: Dict[str, object], page_paths: List[str]):
    urls = [absolute_url(site["base_url"], path) for path in site["existing_pages"]]
    urls.extend(absolute_url(site["base_url"], path) for path in page_paths)
    lines = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">"
    ]
    for url in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{escape(url)}</loc>")
        lines.append("  </url>")
    lines.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_robots(site: Dict[str, object]):
    content = "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            f"Sitemap: {site['base_url']}/sitemap.xml",
            ""
        ]
    )
    (ROOT / "robots.txt").write_text(content, encoding="utf-8")


def main():
    site = load_json(CONTENT_DIR / "site.json")
    counties = {item["id"]: item for item in load_json(CONTENT_DIR / "counties.json")}
    forms = {item["id"]: item for item in load_json(CONTENT_DIR / "forms.json")}
    workflows = {item["id"]: item for item in load_json(CONTENT_DIR / "workflows.json")}
    pages = load_json(CONTENT_DIR / "pages.json")

    generated = []
    warnings = []
    for page in pages:
        context = build_page_context(site, counties, forms, workflows, page)
        output_path = write_page(context, page["slug"])
        generated.append((page["canonical_slug"], output_path))
        for key in ("meta_title", "meta_description", "h1"):
            if not context.get(key):
                warnings.append(f"Missing {key} for {page['id']}")

    write_sitemap(site, [path for path, _ in generated])
    write_robots(site)

    print("Generated SEO pages:")
    for canonical, output_path in generated:
        print(f"- {canonical} -> {output_path.relative_to(ROOT)}")
    print("- /sitemap.xml -> sitemap.xml")
    print("- /robots.txt -> robots.txt")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")


if __name__ == "__main__":
    main()
