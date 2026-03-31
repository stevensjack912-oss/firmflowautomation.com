#!/usr/bin/env python3
"""Generate pSEO/AEO pages for the static FirmFlow site."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from string import Template
from typing import Dict, List, Tuple


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


def absolute_url(base_url: str, path: str) -> str:
    return f"{base_url}{path}"


def page_depth(slug: str) -> int:
    return len(Path(slug).parts)


def form_display_name(form: Dict[str, object], include_name: bool = True) -> str:
    form_name = str(form.get("form_name", "")).strip()
    if include_name and form_name:
        return f"{form['form_number']} {form_name}"
    return str(form["form_number"])


def escape_list(items: List[str]) -> str:
    return "".join(f"<li>{escape(item)}</li>" for item in items)


def render_faq_items(items: List[Dict[str, str]]) -> str:
    blocks = []
    for item in items:
        question = escape(item["question"])
        answer = escape(item["answer"])
        blocks.append(
            "<div class=\"faq-item\">"
            "<button class=\"faq-question\" aria-expanded=\"false\">"
            f"{question}"
            "<svg class=\"faq-chevron\" viewBox=\"0 0 24 24\" aria-hidden=\"true\">"
            "<polyline points=\"6 9 12 15 18 9\"></polyline>"
            "</svg>"
            "</button>"
            "<div class=\"faq-answer\" role=\"region\">"
            f"<div class=\"faq-answer-inner\">{answer}</div>"
            "</div>"
            "</div>"
        )
    return "".join(blocks)


def render_breadcrumbs(crumbs: List[Dict[str, str]]) -> str:
    items = []
    for idx, crumb in enumerate(crumbs):
        label = escape(crumb["label"])
        if idx == len(crumbs) - 1:
            items.append(f"<li aria-current=\"page\"><span>{label}</span></li>")
        else:
            href = escape(crumb["href"], quote=True)
            items.append(f"<li><a href=\"{href}\">{label}</a></li>")
    return load_template("partials/breadcrumbs.html").substitute(
        breadcrumb_items="".join(items)
    )


def render_related_items(links: List[Dict[str, str]]) -> str:
    cards = []
    for link in links:
        cards.append(
            "<article class=\"card seo-related-card\">"
            f"<h3><a href=\"{escape(link['href'], quote=True)}\">{escape(link['title'])}</a></h3>"
            f"<p>{escape(link['body'])}</p>"
            "</article>"
        )
    return "".join(cards)


def render_feature_cards(items: List[Dict[str, str]], card_class: str = "card") -> str:
    cards = []
    for item in items:
        cards.append(
            f"<article class=\"{card_class}\">"
            f"<h3>{escape(item['title'])}</h3>"
            f"<p>{escape(item['body'])}</p>"
            "</article>"
        )
    return "".join(cards)


def render_bullet_columns(columns: List[Dict[str, object]]) -> str:
    blocks = []
    for column in columns:
        blocks.append(
            "<article class=\"seo-note-card\">"
            f"<h3>{escape(column['title'])}</h3>"
            f"<ul class=\"seo-link-list\">{escape_list(column['items'])}</ul>"
            "</article>"
        )
    return "".join(blocks)


def render_definition_split(primary_title: str, primary_body: str, secondary_title: str, secondary_body: str) -> str:
    return (
        "<div class=\"seo-split-grid\">"
        "<article class=\"seo-note-card\">"
        f"<p class=\"seo-kicker\">{escape(primary_title)}</p>"
        f"<p>{escape(primary_body)}</p>"
        "</article>"
        "<article class=\"seo-note-card\">"
        f"<p class=\"seo-kicker\">{escape(secondary_title)}</p>"
        f"<p>{escape(secondary_body)}</p>"
        "</article>"
        "</div>"
    )


def render_section(section_label: str, heading: str, intro: str, inner_html: str, extra_class: str = "") -> str:
    class_suffix = f" seo-section-block {extra_class}".rstrip()
    return (
        f"<section class=\"seo-content-block fade-up{class_suffix}\">"
        "<div class=\"section-header\">"
        f"<span class=\"section-label\">{escape(section_label)}</span>"
        f"<h2>{escape(heading)}</h2>"
        f"<p>{escape(intro)}</p>"
        "</div>"
        f"{inner_html}"
        "</section>"
    )


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
                "url": context["base_url"],
            },
            "about": context["about"],
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": idx + 1,
                    "name": crumb["label"],
                    "item": crumb["absolute_url"],
                }
                for idx, crumb in enumerate(context["breadcrumbs_data"])
            ],
        },
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
                            "text": item["answer"],
                        },
                    }
                    for item in context["faq_items"]
                ],
            }
        )
    return json.dumps(schema, indent=2)


def build_page_lookup(
    pages: List[Dict[str, object]],
) -> Tuple[Dict[str, Dict[str, object]], Dict[str, Dict[str, object]], Dict[str, Dict[str, object]], Dict[Tuple[str, str], Dict[str, object]]]:
    county_pages = {}
    form_pages = {}
    workflow_pages = {}
    county_form_pages = {}
    for page in pages:
        page_type = page["page_type"]
        if page_type == "county":
            county_pages[page["county_id"]] = page
        elif page_type == "form":
            form_pages[page["form_id"]] = page
        elif page_type == "workflow":
            workflow_pages[page["workflow_id"]] = page
        elif page_type == "county_form":
            county_form_pages[(page["county_id"], page["form_id"])] = page
    return county_pages, form_pages, workflow_pages, county_form_pages


def county_link(page: Dict[str, object], county: Dict[str, object], root_path: str, body: str) -> Dict[str, str]:
    return {
        "title": f"{county['county']} Parentage Order Workflow Guide",
        "href": f"{root_path}{page['slug']}/",
        "body": body,
    }


def form_link(page: Dict[str, object], form: Dict[str, object], root_path: str, body: str) -> Dict[str, str]:
    return {
        "title": f"{form['form_number']} in California Parentage Order Workflows",
        "href": f"{root_path}{page['slug']}/",
        "body": body,
    }


def workflow_link(page: Dict[str, object], workflow: Dict[str, object], root_path: str, body: str) -> Dict[str, str]:
    return {
        "title": workflow["h1"],
        "href": f"{root_path}{page['slug']}/",
        "body": body,
    }


def build_page_context(
    site: Dict[str, object],
    counties: Dict[str, Dict[str, object]],
    forms: Dict[str, Dict[str, object]],
    workflows: Dict[str, Dict[str, object]],
    page: Dict[str, object],
    county_pages: Dict[str, Dict[str, object]],
    form_pages: Dict[str, Dict[str, object]],
    workflow_pages: Dict[str, Dict[str, object]],
    county_form_pages: Dict[Tuple[str, str], Dict[str, object]],
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
        related_links = []
        for form_id in county.get("related_forms", [])[:2]:
            if form_id in form_pages:
                related_links.append(
                    form_link(
                        form_pages[form_id],
                        forms[form_id],
                        root_path,
                        "A form-focused explainer showing where a specific statewide document may fit into the broader packet.",
                    )
                )
        if "california-parentage-order-workflow" in workflow_pages:
            related_links.append(
                workflow_link(
                    workflow_pages["california-parentage-order-workflow"],
                    workflows["california-parentage-order-workflow"],
                    root_path,
                    "A staged workflow view covering intake, form prep, county review, and final assembly.",
                )
            )
        related_links = related_links[:3]

        breadcrumbs = [
            {"label": "Home", "href": f"{root_path}index.html", "absolute_url": site["base_url"] + "/index.html"},
            {"label": "Counties", "href": f"{root_path}product.html", "absolute_url": site["base_url"] + "/product.html"},
            {"label": county["county"], "href": "", "absolute_url": context["canonical_url"]},
        ]

        packet_section = render_section(
            "Packet Structure",
            f"What firms often track in {county['county']}",
            county["page_angle"],
            f"<div class=\"seo-feature-grid\">{render_feature_cards(county['common_packet_components'], 'seo-feature-card')}</div>",
        )

        split_columns = [
            {"title": "Who usually uses this page", "items": county["team_roles"]}
        ]
        if county.get("local_forms"):
            split_columns.append({"title": "County-specific forms firms may track", "items": county["local_forms"]})

        variation_section = render_section(
            "Where Variation Shows Up",
            f"{county['county']} review points",
            "County pages are most useful when they call out where firms typically pause to verify the packet instead of pretending every matter follows one fixed recipe.",
            (
                f"<div class=\"seo-split-grid\">"
                f"{render_feature_cards(county['variation_points'], 'seo-note-card')}"
                f"{render_bullet_columns(split_columns)}"
                "</div>"
            ),
        )

        context.update(
            {
                "meta_title": page["meta_title"],
                "meta_description": page["meta_description"],
                "h1": page["h1"],
                "hero_label": "County Guide",
                "hero_aria": f"{county['county']} guide",
                "hero_intro": county["intro_summary"],
                "short_answer": (
                    f"{county['county']} parentage order preparation often involves statewide forms, supporting local documents, and a careful packet review process. "
                    "Exact filing requirements may vary by county, so firms should verify current court and local filing requirements before filing."
                ),
                "workflow_context": county["workflow_context"],
                "faq_items": county["faq_items"],
                "faq_heading": f"{county['county']} workflow FAQ",
                "faq_intro": "These answers are designed to help legal teams understand workflow context without making unverified procedural claims.",
                "related_heading": "Related county workflow resources",
                "related_intro": "Use these supporting pages to move from county-level workflow context into specific forms and broader parentage order planning.",
                "about": [county["county"], "California parentage order workflow"],
                "page_sections": packet_section + variation_section,
            }
        )
        template_name = "county.html"

    elif page_type == "form":
        form = forms[page["form_id"]]
        form_name_long = form_display_name(form, include_name=True)
        form_short = form_display_name(form, include_name=False)
        related_links = []
        for county_id in form.get("related_counties", [])[:2]:
            if county_id in county_pages:
                related_links.append(
                    county_link(
                        county_pages[county_id],
                        counties[county_id],
                        root_path,
                        "A county-focused guide showing how one supported venue can be organized at the packet level.",
                    )
                )
        if "california-parentage-order-workflow" in workflow_pages:
            related_links.append(
                workflow_link(
                    workflow_pages["california-parentage-order-workflow"],
                    workflows["california-parentage-order-workflow"],
                    root_path,
                    "A workflow-level explainer that shows where single-form review fits into the larger process.",
                )
            )
        related_links = related_links[:3]

        breadcrumbs = [
            {"label": "Home", "href": f"{root_path}index.html", "absolute_url": site["base_url"] + "/index.html"},
            {"label": "Forms", "href": f"{root_path}product.html", "absolute_url": site["base_url"] + "/product.html"},
            {"label": form_short, "href": "", "absolute_url": context["canonical_url"]},
        ]

        definition_section = render_section(
            "Form Role",
            f"How teams commonly think about {form_name_long}",
            "Form pages work best when they explain where the document fits operationally, not when they try to stand in for official form instructions.",
            render_definition_split("Definition", form["definition"], "Operational role", form["operational_role"]),
        )
        checkpoints_section = render_section(
            "Review Checkpoints",
            f"Where {form_name_long} often gets reviewed",
            "Many teams use form pages as a practical review map: selection first, then packet relationships, then filing-readiness checks.",
            (
                f"<div class=\"seo-feature-grid\">{render_feature_cards(form['review_checkpoints'], 'seo-feature-card')}</div>"
                f"<div class=\"seo-split-grid seo-split-grid-tight\">{render_feature_cards(form['adjacent_forms'], 'seo-note-card')}</div>"
            ),
        )

        about = [form_short, "California surrogacy filing workflow"]
        if str(form.get("form_name", "")).strip():
            about.append(str(form["form_name"]))

        context.update(
            {
                "meta_title": page["meta_title"],
                "meta_description": page["meta_description"],
                "h1": page["h1"],
                "hero_label": "Form Guide",
                "hero_aria": f"{form_short} guide",
                "hero_intro": form["intro_summary"],
                "short_answer": form["short_answer"],
                "workflow_context": form["workflow_context"],
                "faq_items": form["faq_items"],
                "faq_heading": f"{form_short} FAQ",
                "faq_intro": "These answers are written for workflow education and should not be treated as definitive filing instructions.",
                "related_heading": "Related form and workflow resources",
                "related_intro": "Explore the surrounding workflow context and county pages that relate to this form.",
                "about": about,
                "page_sections": definition_section + checkpoints_section,
            }
        )
        template_name = "form.html"

    elif page_type == "workflow":
        workflow = workflows[page["workflow_id"]]
        related_links = []
        for county_id in workflow.get("related_counties", [])[:2]:
            if county_id in county_pages:
                related_links.append(
                    county_link(
                        county_pages[county_id],
                        counties[county_id],
                        root_path,
                        "A county-level guide showing how a supported venue organizes packet planning and county-specific review.",
                    )
                )
        for form_id in workflow.get("related_forms", [])[:1]:
            if form_id in form_pages:
                related_links.append(
                    form_link(
                        form_pages[form_id],
                        forms[form_id],
                        root_path,
                        "A form page that helps teams connect one document number to the larger workflow.",
                    )
                )
        related_links = related_links[:3]

        breadcrumbs = [
            {"label": "Home", "href": f"{root_path}index.html", "absolute_url": site["base_url"] + "/index.html"},
            {"label": "Workflows", "href": f"{root_path}product.html", "absolute_url": site["base_url"] + "/product.html"},
            {"label": workflow["h1"], "href": "", "absolute_url": context["canonical_url"]},
        ]

        stages_section = render_section(
            "Workflow Stages",
            "A staged view of the process",
            "Workflow pages should do one thing clearly: show the sequence firms commonly use to move from intake to filing-ready packet review.",
            f"<div class=\"seo-feature-grid\">{render_feature_cards(workflow['stages'], 'seo-feature-card')}</div>",
        )
        handoff_section = render_section(
            "Handoffs and Risks",
            "Where workflows usually succeed or break",
            "This is where workflow pages can be more useful than form pages: they can describe how the work moves between people and where review problems usually appear.",
            f"<div class=\"seo-split-grid\">{render_feature_cards(workflow['handoff_points'], 'seo-note-card')}{render_feature_cards(workflow['review_risks'], 'seo-note-card')}</div>",
        )

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
                "faq_items": workflow["faq_items"],
                "faq_heading": "Workflow FAQ",
                "faq_intro": "These answers are designed to make the workflow easy to understand and quote cleanly while staying cautious about local variation.",
                "related_heading": "Related workflow resources",
                "related_intro": "Use these links to move from broad workflow education into county-specific and form-specific context.",
                "about": [workflow["h1"], "Surrogacy law firm automation"],
                "page_sections": stages_section + handoff_section,
            }
        )
        template_name = "workflow.html"

    else:
        county = counties[page["county_id"]]
        form = forms[page["form_id"]]
        form_name_long = form_display_name(form, include_name=True)
        form_short = form_display_name(form, include_name=False)
        related_links = []
        if page["county_id"] in county_pages:
            related_links.append(
                county_link(
                    county_pages[page["county_id"]],
                    county,
                    root_path,
                    "Step back to the broader county page if you want venue-level workflow context instead of one form-specific angle.",
                )
            )
        if page["form_id"] in form_pages:
            related_links.append(
                form_link(
                    form_pages[page["form_id"]],
                    form,
                    root_path,
                    "Compare this county-plus-form page with the broader form page that explains the document’s role in the overall packet.",
                )
            )
        if "california-parentage-order-workflow" in workflow_pages:
            related_links.append(
                workflow_link(
                    workflow_pages["california-parentage-order-workflow"],
                    workflows["california-parentage-order-workflow"],
                    root_path,
                    "A workflow page that shows how county-specific and form-specific review fit into one larger process.",
                )
            )

        breadcrumbs = [
            {"label": "Home", "href": f"{root_path}index.html", "absolute_url": site["base_url"] + "/index.html"},
            {"label": "Counties", "href": f"{root_path}product.html", "absolute_url": site["base_url"] + "/product.html"},
            {
                "label": county["county"],
                "href": f"{root_path}{county_pages[page['county_id']]['slug']}/",
                "absolute_url": site["base_url"] + county_pages[page["county_id"]]["canonical_slug"],
            },
            {"label": form_short, "href": "", "absolute_url": context["canonical_url"]},
        ]

        narrow_section = render_section(
            "Why This Query Matters",
            f"Why teams search for {county['county']} + {form_short}",
            "County-plus-form pages should feel narrower than county pages and more situational than form pages. The goal is to explain the relationship, not repeat both pages in miniature.",
            render_definition_split(
                "What they usually want to know",
                f"Searchers looking for {county['county']} and {form_short} together are often trying to understand whether that form belongs in the county-specific packet they are building.",
                "What this page can answer",
                f"This page focuses on how {form_name_long} may fit inside a {county['county']} workflow, while still keeping county requirements and matter facts as variables that must be verified.",
            ),
        )
        fit_section = render_section(
            "Workflow Fit",
            f"How {form_name_long} may fit into a {county['county']} packet",
            "This is the useful part of a county-plus-form page: it can show how a specific form sits inside venue-aware packet planning without pretending the page is a filing instruction sheet.",
            (
                f"<div class=\"seo-feature-grid\">{render_feature_cards(form['review_checkpoints'], 'seo-feature-card')}</div>"
                f"<div class=\"seo-split-grid\">{render_bullet_columns([{'title': 'County-aware reminders', 'items': county['county_notes'] + form['county_notes']}])}</div>"
            ),
        )

        faq_items = county["faq_items"][:1] + form["faq_items"][:1]
        about = [county["county"], form_short, "California parentage order workflow"]
        if str(form.get("form_name", "")).strip():
            about.append(str(form["form_name"]))

        context.update(
            {
                "meta_title": page["meta_title"],
                "meta_description": page["meta_description"],
                "h1": page["h1"],
                "hero_label": "County + Form Guide",
                "hero_aria": f"{county['county']} {form_short} guide",
                "hero_intro": (
                    f"{form_name_long} is commonly reviewed as part of broader California parentage workflows, "
                    f"and legal teams working in {county['county']} often want a cleaner way to understand where it may fit in the packet."
                ),
                "short_answer": (
                    f"In {county['county']}, {form_name_long} may be reviewed as part of a broader parentage order packet. "
                    "The exact filing set may vary by county practice and by matter, so firms should verify current requirements before filing."
                ),
                "workflow_context": (
                    f"A county-aware workflow helps teams understand how {form_name_long} may relate to the rest of a {county['county']} filing packet, "
                    "while still leaving room for matter-specific attorney review."
                ),
                "faq_items": faq_items,
                "faq_heading": f"{county['county']} + {form_short} FAQ",
                "faq_intro": "These answers are intentionally narrow and workflow-focused so they support planning without overstating county procedure.",
                "related_heading": "Related county and form resources",
                "related_intro": "Move from this narrow page into the broader county and form views that surround it.",
                "about": about,
                "page_sections": narrow_section + fit_section,
            }
        )
        template_name = "county_form.html"

    context["related_links"] = load_template("partials/related_links.html").substitute(
        related_heading=context["related_heading"],
        related_intro=context["related_intro"],
        related_items=render_related_items(related_links),
    )
    context["summary_block"] = load_template("partials/summary_block.html").substitute(
        short_answer=context["short_answer"],
        workflow_context=context["workflow_context"],
    )
    context["faq_section"] = load_template("partials/faq_section.html").substitute(
        faq_heading=context["faq_heading"],
        faq_intro=context["faq_intro"],
        faq_items=render_faq_items(context["faq_items"]),
    )
    context["disclaimer"] = load_template("partials/disclaimer.html").substitute(
        disclaimer=context["disclaimer"]
    )
    context["breadcrumbs"] = render_breadcrumbs(breadcrumbs)
    context["breadcrumbs_data"] = breadcrumbs
    context["body_content"] = load_template(template_name).substitute(context)
    context["head_meta"] = load_template("partials/head_meta.html").substitute(
        meta_title=context["meta_title"],
        meta_description=context["meta_description"],
        canonical_url=context["canonical_url"],
        site_name=site["site_name"],
        og_image=site["organization"]["logo"],
    )
    context["schema_json"] = build_schema(context)
    return context


def write_page(context: Dict[str, object], slug: str) -> Path:
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
        "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">",
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
            "",
        ]
    )
    (ROOT / "robots.txt").write_text(content, encoding="utf-8")


def main():
    site = load_json(CONTENT_DIR / "site.json")
    counties = {item["id"]: item for item in load_json(CONTENT_DIR / "counties.json")}
    forms = {item["id"]: item for item in load_json(CONTENT_DIR / "forms.json")}
    workflows = {item["id"]: item for item in load_json(CONTENT_DIR / "workflows.json")}
    pages = load_json(CONTENT_DIR / "pages.json")
    county_pages, form_pages, workflow_pages, county_form_pages = build_page_lookup(pages)

    generated = []
    warnings = []
    for page in pages:
        context = build_page_context(
            site,
            counties,
            forms,
            workflows,
            page,
            county_pages,
            form_pages,
            workflow_pages,
            county_form_pages,
        )
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
