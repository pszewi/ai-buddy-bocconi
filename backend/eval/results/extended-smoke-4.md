# Extended Evaluation Results

## R01
Question: From Linate Airport to central Milan by metro M4, how long does it take to reach San Babila, what are the operating hours and frequency, and how much is an ordinary ticket?
Expected verticale: relocation
Returned verticale: relocation
Category: informative
Latency: 9.2s
Status: 200

Expected facts:
M4 reaches San Babila in 12 minutes from Linate Aeroporto. Service runs about 05:40-00:20, every 3-6 minutes. Ordinary ticket costs EUR 2.20 and is valid for 90 minutes.

Answer:
The retrieved sources do not mention "M4" in relation to this question, so I cannot answer it reliably. I will not apply a generic deadline, amount, rule, or result to a specific item that is not present in the sources.

Expected sources:
- relocation/www-aeroporto-net-aeroporto-milano-linate-collegamenti-aeroporto-milano-linate.md

Returned sources:
- relocation/www-aeroporto-net-aeroporto-milano-linate-collegamenti-aeroporto-milano-linate.md
- relocation/www-unibocconi-it-en-campus-buildings-and-classrooms-how-reach-bocconi-campus.md
- relocation/www-malpensashuttle-it-en.md

## L03
Question: What medical certificate is valid for Bocconi Sport registration, and how must it be submitted?
Expected verticale: life_on_campus
Returned verticale: life_on_campus
Category: actionable
Latency: 12.9s
Status: 200

Expected facts:
Accepted options are a non-competitive sports medical certificate with a valid ECG, issued by a Sports Medicine Center, sports medicine specialist, or GP/family doctor, or a competitive sports certificate issued by a Sports Medicine Center. If issued by a GP/family doctor, a signed self-declaration is required. Recreational/motor activity certificates and Virgin Active certificates are not accepted. Upload via the you@B app widget Bocconi Sport > Medical Certificate.

Answer:
To register for Bocconi Sport, a valid medical certificate must be uploaded via the you@B app in the widget Bocconi Sport > Medical Certificate.

There are two valid categories of medical certificates:

1. **For non-competitive sports activities:**  
   - The certificate must include a valid ECG (electrocardiogram).  
   - It must be issued by a Sports Medicine Center, a Specialist in Sports Medicine, or your general practitioner/family doctor.  
   - If issued by your general practitioner/family doctor, you must also provide a signed self-declaration (template available) confirming under your responsibility that the doctor who issued the certificate is your general practitioner/family doctor. Without this declaration, the certificate will NOT be accepted.  
   - Uploading the ECG tracing separately is NOT valid. The term “ECG” must be explicitly stated on the certificate.  
   - The certificate must be issued by an Italian doctor and written in Italian.  
   - The medical certificate must include the statement “copia conforme all’originale in mio possesso” with the date and signature of the certificate holder.

2. **For competitive sports activities:**  
   - Certificate issued by a Sports Medicine Center (must be in Italian and still valid).  
   - Must be uploaded online via the you@B app, in the same widget.

Certificates for recreational or motor activity are NOT valid, and certificates obtained by Virgin Active are NOT accepted for Bocconi Sport activities.

**Summary on submission:**  
Upload the properly completed medical certificate through the you@B app, in the Bocconi Sport > Medical Certificate widget, including all required statements, signatures, and the ECG explicitly stated for non-competitive certificates.

Expected sources:
- life_on_campus/www-bocconisport-eu-en-news-medical-certificate.md

Returned sources:
- life_on_campus/www-bocconisport-eu-en-news-medical-certificate.md
- life_on_campus/www-bocconisport-eu-en-news-bocconi-sport-membership.md
- life_on_campus/www-bocconisport-eu-en-support-programs-student-athletes.md

## S03
Question: For incoming exchange students in Fall 2026, when is course selection, when is add/drop, how many courses may they select, and can they add language courses?
Expected verticale: study_abroad
Returned verticale: study_abroad
Category: computational
Latency: 9.544s
Status: 200

Expected facts:
Course Selection for Fall AY 2026-2027 runs August 24-26, 2026 through yoU@B, first come-first served with no waiting list. Add/Drop is September 7-15, 2026. Exchange students must enroll in minimum 1 and maximum 5 courses per semester. They cannot add language courses to their study plan.

Answer:
For incoming exchange students in Fall 2026 at Bocconi University:

- **Course Selection** will take place from August 24 to 26, 2026, via the yoU@B student diary.
- The **Add/Drop period** runs from September 7 to 15, 2026. After this deadline, no changes to the study plan are allowed.
- Students may select **a minimum of 1 and a maximum of 5 courses** per semester.
- Exchange students **can add Italian language courses**, such as the optional Italian Language Crash Course offered from August 25 to September 5, 2026. However, this course is extracurricular, does not grant credits, and does not appear in the official study plan or transcript.

This means language courses can be taken in addition to the 1 to 5 regular Bocconi courses chosen during course selection.

Sources: [1], [2], [5]

Expected sources:
- study_abroad/www-unibocconi-it-en-international-students-incoming-exchange-students-academics-exchange-students-course-selection.md

Returned sources:
- study_abroad/www-unibocconi-it-en-international-students-incoming-exchange-students-academics-exchange-students-course-selection.md
- study_abroad/www-unibocconi-it-en-international-students-incoming-exchange-students-academics-exchange-students-academic-calendar-202.md
- study_abroad/www-unibocconi-it-sites-default-files-090524-bocconi-20fact-20sheet-202024-2025-20printable-20version-pdf.md
- study_abroad/www-unibocconi-it-en-international-students-incoming-exchange-students-educational-offer-incoming-exchange-students.md
- study_abroad/www-unibocconi-it-en-international-students-incoming-exchange-students-italian-language-courses.md

## C02
Question: Compare one-year placement for MSc Finance and MSc Data Science and Business Analytics: employment rate, share working abroad, and continuing-studies figure if available.
Expected verticale: career_readiness
Returned verticale: career_readiness
Category: computational
Latency: 10.506s
Status: 200

Expected facts:
Finance: 93% employed, 63.9% of employed graduates work abroad. DSBA: 93.2% employed, 39% of employed graduates work abroad, and 12% are continuing their studies. Finance source does not list a continuing-studies figure in the same section.

Answer:
Here is the comparison of one-year placement outcomes for MSc Finance and MSc Data Science and Business Analytics at Bocconi University, based on data from academic year 2021-2022 and 2022-2023 graduates:

**Employment Rate (one year after graduation):**  
- MSc Finance: 93% employed  
- MSc Data Science and Business Analytics: Between 93.2% (a.y. 2021-22) and 95.6% (a.y. 2022-23) employed  

**Share Working Abroad (one year after graduation):**  
- MSc Finance: 63.9% of employed graduates work abroad  
- MSc Data Science and Business Analytics: Ranges from 39% (a.y. 2021-22) to 46.5% (a.y. 2022-23)  

**Continuing Studies (one year after graduation):**  
- MSc Finance: No data provided in excerpts  
- MSc Data Science and Business Analytics: 12% (a.y. 2021-22), but only 4.3% for a.y. 2022-23 graduates  

Summary: Both programs have high employment rates above 93% one year after graduation. MSc Finance graduates have a notably higher share working abroad (~64%) compared to MSc Data Science and Business Analytics graduates (~39-46%). MSc Data Science and Business Analytics graduates also show some continuing studies (4-12%), while no continuing studies data is provided for MSc Finance.

Expected sources:
- career_readiness/www-unibocconi-it-en-current-students-master-science-program-finance-placement-and-program-performance.md
- career_readiness/www-unibocconi-it-en-current-students-master-science-program-data-science-and-business-analytics-placement-and-program-p.md

Returned sources:
- career_readiness/www-unibocconi-it-en-current-students-master-science-program-data-science-and-business-analytics-placement-and-program-p.md
- career_readiness/www-unibocconi-it-en-current-students-master-science-program-finance-placement-and-program-performance.md
- career_readiness/www-unibocconi-it-en-programs-master-science-data-science-and-business-analytics-program-placement.md
- career_readiness/www-unibocconi-it-en-programs-master-science-data-science-and-business-analytics-career-opportunities.md
- career_readiness/www-unibocconi-it-en-programs-master-science-data-science-and-business-analytics.md

