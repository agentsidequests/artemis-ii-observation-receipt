# Public Link Audit

Audit date: 2026-10-10

Scope: every distinct public URL linked from `PUBLIC-ANALYSIS-DRAFT.md`.

Method: direct HTTP GET requests were issued with response-body streaming disabled after headers. This verifies reachability at the audit time. It does not verify future availability, reader permissions, or the accuracy of the linked material.

Result: `22 / 22` distinct links returned HTTP `200 OK`. The October 10 revision removed the OAM-TCD and IRRISIGHT links and added four directly rechecked OGC, SomBench, and MCTED links.

## Audited links

- `https://arxiv.org/abs/2509.08027`
- `https://arxiv.org/abs/2609.13277`
- `https://docs.ogc.org/is/23-008r5/23-008r5.html`
- `https://ntrs.nasa.gov/citations/20260009223`
- `https://pds-data-dictionaries.github.io/ldd-ml/user/user-guide.html`
- `https://pds-geosciences.wustl.edu/artemis2/urn-nasa-pds-artemis2_mission/document/artemis2_data_user_guide.pdf`
- `https://pds-geosciences.wustl.edu/artemis2/urn-nasa-pds-artemis2_mission/document/artemis2_osdmp.pdf`
- `https://pds-geosciences.wustl.edu/missions/artemis2/mission.htm`
- `https://pds.nasa.gov/data/pds4/documents/document_pds4_standards/1.26.0.0/PDS4_DPH_1.26.0.pdf`
- `https://pds.nasa.gov/datastandards/dictionaries/index-1.25.0.0.shtml`
- `https://pds.nasa.gov/datastandards/documents/dd/current/PDS4_PDS_DD_1J00/webhelp/all/ch03s111.html`
- `https://pds.nasa.gov/datastandards/documents/dd/current/PDS4_PDS_DD_1J00/webhelp/all/ch03s52.html`
- `https://pds.nasa.gov/datastandards/documents/dd/current/PDS4_PDS_DD_1J00/webhelp/all/ch03s70.html`
- `https://pds.nasa.gov/home/proposers/archiving/`
- `https://pds.nasa.gov/pds4/ml/v1/PDS4_ML_1P00_1211.JSON`
- `https://pmc.ncbi.nlm.nih.gov/articles/PMC9908044/`
- `https://science.nasa.gov/researchers/science-information-policy_faq/`
- `https://science.nasa.gov/wp-content/uploads/2023/05/PDEIRBFinalReport-1.pdf`
- `https://science.nasa.gov/wp-content/uploads/2024/03/psd-pde-irb-response-v1-20240228.pdf`
- `https://www.nasa.gov/blogs/artemis/2026/10/07/nasa-releases-artemis-ii-lunar-science-data-images/`
- `https://www.ogc.org/standards/trainingdml-ai/`
- `https://www.wired.com/story/nasa-just-made-nearly-1-tb-of-artemis-ii-data-available-to-the-public/`
