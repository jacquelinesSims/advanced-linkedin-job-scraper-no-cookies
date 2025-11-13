# Advanced Linkedin Job Scraper (No Cookies)

> This scraper pulls fresh LinkedIn job listings at scale without accounts, cookies, or risky workarounds. It handles bulk job searches, complex filters, and delivers full job and company insights in clean structured data.
>
> It’s built for people who need fast, high-volume LinkedIn job data without the usual friction.


<p align="center">
  <a href="https://bitbash.dev" target="_blank">
    <img src="https://github.com/za2122/footer-section/blob/main/media/scraper.png" alt="Bitbash Banner" width="100%"></a>
</p>
<p align="center">
  <a href="https://t.me/devpilot1" target="_blank">
    <img src="https://img.shields.io/badge/Chat%20on-Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram">
  </a>&nbsp;
  <a href="https://wa.me/923249868488?text=Hi%20BitBash%2C%20I'm%20interested%20in%20automation." target="_blank">
    <img src="https://img.shields.io/badge/Chat-WhatsApp-25D366?style=for-the-badge&logo=whatsapp&logoColor=white" alt="WhatsApp">
  </a>&nbsp;
  <a href="mailto:sale@bitbash.dev" target="_blank">
    <img src="https://img.shields.io/badge/Email-sale@bitbash.dev-EA4335?style=for-the-badge&logo=gmail&logoColor=white" alt="Gmail">
  </a>&nbsp;
  <a href="https://bitbash.dev" target="_blank">
    <img src="https://img.shields.io/badge/Visit-Website-007BFF?style=for-the-badge&logo=google-chrome&logoColor=white" alt="Website">
  </a>
</p>




<p align="center" style="font-weight:600; margin-top:8px; margin-bottom:8px;">
  Created by Bitbash, built to showcase our approach to Scraping and Automation!<br>
  If you are looking for <strong>Advanced Linkedin Job Scraper (No Cookies)</strong> you've just found your team — Let’s Chat. 👆👆
</p>


## Introduction

This project collects detailed job listings and company data from LinkedIn using job titles, locations, companies, and multiple filter options.
It solves the bottleneck of slow manual job gathering and gives teams a dependable way to research hiring trends, competitors, and markets.

It’s useful for recruiters, analysts, founders, and data teams who want curated job intelligence delivered in a predictable, automated workflow.

### Why This Scraper Matters

- Handles multi-title and multi-location bulk scraping.
- Retrieves full job details including salary, benefits, company profiles, and job statistics.
- Works with fast, concurrency-powered processing.
- Supports deep filtering like experience level, job type, workplace type, and salary range.
- No credentials or cookies required, reducing risk and complexity.

## Features

| Feature | Description |
|--------|-------------|
| No-login scraping | Runs without accounts, cookies, or session handling, reducing friction and risk. |
| Multi-job-title support | Scrape multiple job roles in a single run for bulk research or sourcing. |
| Location-aware search | Uses LinkedIn autocomplete logic for accurate regional mapping. |
| Rich job details | Extracts descriptions, salary, job type, applicants, posting age, and more. |
| Company data enrichment | Pulls employee counts, industries, logo URLs, and HQ info. |
| High concurrency | Processes multiple listings in parallel to speed up large jobs. |
| Advanced filters | Narrow results by employment type, workplace type, salary, easy apply, under 10 applicants, and posted date. |
| Industry filtering | Supports filtering by LinkedIn industry IDs for niche targeting. |
| Max results control | Set limits per search or pull all available pages up to ~40 pages. |

---

## What Data This Scraper Extracts

| Field Name | Field Description |
|------------|------------------|
| id | Unique job ID for the listing. |
| title | Job title as shown on LinkedIn. |
| linkedinUrl | Direct link to the listing. |
| jobState | Current availability state (e.g., LISTED). |
| postedDate | Date and time when the job was posted. |
| descriptionText | Clean text version of the job description. |
| descriptionHtml | HTML-formatted description. |
| location | Parsed and raw location information. |
| employmentType | Full-time, part-time, contract, etc. |
| workplaceType | Remote, hybrid, on-site. |
| salary | Salary range and metadata. |
| company | Full company object with profile data. |
| benefits | List of stated job benefits. |
| applicants | Applicant count. |
| views | Listing view count. |
| applyMethod | Application link and method. |
| jobFunctions | Functional categories of the role. |
| expireAt | Estimated expiration date of listing. |

---

## Example Output


    {
        "id": "4227647589",
        "title": "Associate Data Engineer",
        "linkedinUrl": "https://www.linkedin.com/jobs/view/4227647589/",
        "jobState": "LISTED",
        "postedDate": "2025-05-14T17:12:41.000Z",
        "descriptionText": "About the Company\nEast Daley Analytics...",
        "descriptionHtml": "<p><b>About the Company</b></p>...",
        "location": {
            "linkedinText": "Greenwood Village, CO",
            "parsed": {
                "text": "Greenwood Village, CO, United States",
                "state": "Colorado",
                "city": "Greenwood Village"
            }
        },
        "employmentType": "full_time",
        "workplaceType": "on_site",
        "salary": {
            "text": "80,000 - 85,000 USD",
            "min": 80000,
            "max": 85000,
            "currency": "USD"
        },
        "company": {
            "name": "East Daley Analytics",
            "employeeCount": 34,
            "linkedinUrl": "https://www.linkedin.com/company/east-daley-analytics"
        },
        "applicants": 1,
        "views": 2
    }

---

## Directory Structure Tree


    Advanced Linkedin Job Scraper (No Cookies)/
    ├── src/
    │   ├── runner.py
    │   ├── extractors/
    │   │   ├── linkedin_job_parser.py
    │   │   ├── company_parser.py
    │   │   └── utils_location.py
    │   ├── outputs/
    │   │   └── exporters.py
    │   └── config/
    │       └── settings.example.json
    ├── data/
    │   ├── inputs.sample.json
    │   └── sample_output.json
    ├── requirements.txt
    └── README.md

---

## Use Cases

- **Recruiters** use it to collect targeted job listings automatically, so they can source candidates faster.
- **Market analysts** use the data to monitor hiring trends, salary shifts, and company expansion patterns.
- **Startups** analyze competitor hiring to guide product decisions and growth strategy.
- **Data teams** integrate job data into dashboards for internal analytics and insights.
- **Researchers** gather large datasets to study labor market behavior without manual collection.

---

## FAQs

**Does this scraper require a LinkedIn account?**
No, it runs entirely without login sessions or cookies while still returning fresh results.

**How accurate is location filtering?**
It uses LinkedIn’s autocomplete suggestions, which improves matching. However, ambiguous queries like “UK” may resolve incorrectly, so using full region names is recommended.

**Can I filter by job type, experience level, or salary?**
Yes, it supports employmentType, workplaceType, experienceLevel, posted date, salary range, and more.

**How many jobs can I extract per run?**
You can set a maxItems limit or pull all available pages for each query, typically up to around 40 pages.

---

## Performance Benchmarks and Results

**Primary Metric:** Processes roughly 1,000 LinkedIn job records in about two minutes thanks to concurrent execution.
**Reliability Metric:** Maintains a high success rate across varying job queries and filters with consistent output formatting.
**Efficiency Metric:** Scrapes six jobs simultaneously per worker, improving throughput on multi-title batches.
**Quality Metric:** Delivers complete job descriptions, accurate salary data, and enriched company profiles with minimal missing fields.


<p align="center">
<a href="https://calendar.app.google/74kEaAQ5LWbM8CQNA" target="_blank">
  <img src="https://img.shields.io/badge/Book%20a%20Call%20with%20Us-34A853?style=for-the-badge&logo=googlecalendar&logoColor=white" alt="Book a Call">
</a>
  <a href="https://www.youtube.com/@bitbash-demos/videos" target="_blank">
    <img src="https://img.shields.io/badge/🎥%20Watch%20demos%20-FF0000?style=for-the-badge&logo=youtube&logoColor=white" alt="Watch on YouTube">
  </a>
</p>
<table>
  <tr>
    <td align="center" width="33%" style="padding:10px;">
      <a href="https://youtu.be/MLkvGB8ZZIk" target="_blank">
        <img src="https://github.com/za2122/footer-section/blob/main/media/review1.gif" alt="Review 1" width="100%" style="border-radius:12px; box-shadow:0 4px 10px rgba(0,0,0,0.1);">
      </a>
      <p style="font-size:14px; line-height:1.5; color:#444; margin:0 15px;">
        “Bitbash is a top-tier automation partner, innovative, reliable, and dedicated to delivering real results every time.”
      </p>
      <p style="margin:10px 0 0; font-weight:600;">Nathan Pennington
        <br><span style="color:#888;">Marketer</span>
        <br><span style="color:#f5a623;">★★★★★</span>
      </p>
    </td>
    <td align="center" width="33%" style="padding:10px;">
      <a href="https://youtu.be/8-tw8Omw9qk" target="_blank">
        <img src="https://github.com/za2122/footer-section/blob/main/media/review2.gif" alt="Review 2" width="100%" style="border-radius:12px; box-shadow:0 4px 10px rgba(0,0,0,0.1);">
      </a>
      <p style="font-size:14px; line-height:1.5; color:#444; margin:0 15px;">
        “Bitbash delivers outstanding quality, speed, and professionalism, truly a team you can rely on.”
      </p>
      <p style="margin:10px 0 0; font-weight:600;">Eliza
        <br><span style="color:#888;">SEO Affiliate Expert</span>
        <br><span style="color:#f5a623;">★★★★★</span>
      </p>
    </td>
    <td align="center" width="33%" style="padding:10px;">
      <a href="https://youtube.com/shorts/6AwB5omXrIM" target="_blank">
        <img src="https://github.com/za2122/footer-section/blob/main/media/review3.gif" alt="Review 3" width="35%" style="border-radius:12px; box-shadow:0 4px 10px rgba(0,0,0,0.1);">
      </a>
      <p style="font-size:14px; line-height:1.5; color:#444; margin:0 15px;">
        “Exceptional results, clear communication, and flawless delivery. Bitbash nailed it.”
      </p>
      <p style="margin:10px 0 0; font-weight:600;">Syed
        <br><span style="color:#888;">Digital Strategist</span>
        <br><span style="color:#f5a623;">★★★★★</span>
      </p>
    </td>
  </tr>
</table>
