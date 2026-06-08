"""Database seeding logic — REAL demo data with full Indian legal documents."""
import os
from sqlmodel import select
from app.core.database import async_session_factory
from app.services.knowledge_graph_service import kg_service
from app.models.tables import (
    Organization, PlaybookRule, EnforceabilityBenchmark,
    RegulatoryUpdate, RegulatoryAlert, ContractTemplate,
    Obligation, AutomationLog, AuditTrailEntry,
    Contract, ContractClause, ContractVersion,
    ApprovalStage, ContractComment,
    ContractTreeIndex, ContractEmbedding,
    ClauseHighlight, PlainEnglishSummary,
)


# ─────────────────────────────────────────────────────────────────────────────
# FULL CONTRACT DOCUMENTS (realistic Indian legal text with embedded PII)
# ─────────────────────────────────────────────────────────────────────────────

NDA_TEXT = """# MUTUAL NON-DISCLOSURE AGREEMENT

## Date: 15 January 2025

## Parties

**Party 1:** Acme Manufacturing Pvt Ltd, a company incorporated under the Companies Act, 2013, having its registered office at Plot 42, Industrial Estate, Pune, Maharashtra 411001, India. CIN: U29120MH2015PTC123456. GSTIN: 27AABCU9603R1ZX.

**Party 2:** InnoTech Solutions Pvt Ltd, a company incorporated under the Companies Act, 2013, having its registered office at 301, Cyber Towers, Hitech City, Hyderabad, Telangana 500081, India. CIN: U72900TG2018PTC123789. GSTIN: 36AABCI8899R1ZP.

**Contact Person (Acme):** Rajesh Sharma, Director — Email: rajesh.sharma@acmemfg.in | Phone: +91 98765 43210 | UPI: rajesh.sharma@okicici

**Contact Person (InnoTech):** Priya Nair, CEO — Email: priya.nair@innotech.in | Phone: +91 99887 66554 | PAN: BNTPS1234K

## 1. Purpose

The Parties wish to explore a potential business relationship for the development of IoT-enabled manufacturing monitoring systems. In connection with this evaluation, each Party may disclose certain Confidential Information to the other Party.

## 2. Definition of Confidential Information

"Confidential Information" means any and all non-public, proprietary, confidential, or trade secret information disclosed by one Party (the "Disclosing Party") to the other Party (the "Receiving Party"), whether in writing, orally, electronically, or by any other means. Confidential Information includes but is not limited to:

- Technical data, know-how, research, product plans, software code, algorithms
- Business plans, financial projections, customer lists, pricing strategies
- Manufacturing processes, quality control protocols, supply chain details
- Personal data of employees including Aadhaar numbers (e.g., 1234 5678 9012) and PAN (ABCDE1234F)

## 3. Obligations of Receiving Party

The Receiving Party agrees to:

(a) Hold all Confidential Information in strict confidence using at least the same degree of care it uses to protect its own confidential information, but in no event less than reasonable care;

(b) Not disclose Confidential Information to any third parties except to those employees, agents, or consultants who have a strict need to know and are bound by confidentiality obligations no less protective than those contained herein;

(c) Not use Confidential Information for any purpose other than evaluating the potential business relationship;

(d) Comply with the Digital Personal Data Protection Act, 2023 (DPDP Act) and obtain free, specific, informed, unconditional, and unambiguous consent before processing any personal data per Section 12.

## 4. Exceptions

The obligations in Section 3 shall not apply to information that:

(a) Is or becomes publicly available through no breach of this Agreement;
(b) Was rightfully in the Receiving Party's possession prior to disclosure;
(c) Is rightfully disclosed to the Receiving Party by a third party without restriction;
(d) Is independently developed by the Receiving Party without use of or reference to Confidential Information.

## 5. Term

This Agreement shall commence on the date first written above and shall remain in effect for a period of three (3) years unless earlier terminated by either Party with thirty (30) days written notice.

## 6. Return of Information

Upon termination of this Agreement or upon written request of the Disclosing Party, the Receiving Party shall promptly return or destroy all Confidential Information and certify such destruction in writing within fifteen (15) days.

## 7. Remedies

Each Party acknowledges that breach of this Agreement may cause irreparable harm for which monetary damages would be inadequate. Accordingly, each Party shall be entitled to seek injunctive relief in addition to all other remedies available at law or in equity.

## 8. Governing Law and Jurisdiction

This Agreement shall be governed by and construed in accordance with the laws of India. Any dispute arising out of or in connection with this Agreement shall be subject to the exclusive jurisdiction of the courts at Mumbai, Maharashtra.

## 9. Independent Contractors

The Parties are independent contractors. Nothing in this Agreement shall be construed to create a partnership, joint venture, or agency relationship.

## 10. Severability

If any provision of this Agreement is held invalid or unenforceable, the remaining provisions shall continue in full force and effect.

## Signatures

**For Acme Manufacturing Pvt Ltd:**

Name: Rajesh Sharma
Title: Director
Date: 15 January 2025
Aadhaar: 9876 5432 1098

**For InnoTech Solutions Pvt Ltd:**

Name: Priya Nair
Title: CEO
Date: 15 January 2025
PAN: BNTPS1234K
"""

VENDOR_TEXT = """# VENDOR SUPPLY AGREEMENT

## Date: 01 March 2024

## Parties

**Buyer:** Acme Manufacturing Pvt Ltd ("Acme"), CIN U29120MH2015PTC123456, GSTIN 27AABCU9603R1ZX, registered at Plot 42, Industrial Estate, Pune, Maharashtra 411001. Contact: Vikram Rao, Procurement Head — vikram.rao@acmemfg.in | +91 87654 32109

**Vendor:** TechSupply Solutions Pvt Ltd ("Vendor"), CIN U31909MH2010PTC201234, GSTIN 27AAACB1234A1Z5, registered at 501, Tower B, Bandra Kurla Complex, Mumbai 400051. Contact: Amit Patel, Business Head — amit.patel@techsupply.in | +91 91234 56789

## 1. Scope of Work

Vendor shall supply precision CNC machined components as per the technical specifications and delivery schedules attached hereto as Schedule A. The components shall conform to ISO 9001:2015 quality standards and Acme's internal QC protocols.

## 2. Term

This Agreement shall commence on 01 March 2024 and continue until 28 February 2026, unless terminated earlier in accordance with Section 9. The Agreement shall automatically renew for successive one (1) year periods unless either Party provides written notice of non-renewal at least ninety (90) days prior to expiration.

## 3. Pricing and Payment Terms

(a) The total contract value is INR 50,00,000 (Rupees Fifty Lakhs Only) per annum, exclusive of GST.

(b) Vendor shall raise monthly invoices by the 5th of each month for deliveries made in the preceding month.

(c) Acme shall make payment within forty-five (45) days from the date of receipt of a valid tax invoice (Net 45).

(d) Late payments shall attract interest at 1.5% per month or the maximum rate permissible under the Reserve Bank of India guidelines, whichever is lower.

(e) All payments shall be made via NEFT/RTGS to Vendor's bank account:
   Bank: HDFC Bank Ltd
   Account: 12345678901234
   IFSC: HDFC0000123
   UPI: techsupply@okhdfcbank

## 4. Delivery

(a) Vendor shall deliver FOB Pune within fifteen (15) business days of receiving a purchase order.

(b) Title and risk of loss shall pass to Acme upon acceptance at the designated delivery location.

(c) Vendor shall maintain minimum safety stock equivalent to thirty (30) days of Acme's average consumption.

## 5. Quality Assurance

(a) All components shall be subject to Acme's incoming quality inspection. Rejection rate shall not exceed 0.5%.

(b) Vendor shall provide material test certificates, dimensional reports, and surface finish data with each shipment.

(c) Acme reserves the right to conduct annual supplier audits with fifteen (15) days prior notice.

## 6. Intellectual Property

All drawings, designs, tooling, and specifications provided by Acme shall remain Acme's exclusive property. Vendor shall not use Acme's IP for any third party without express written consent.

## 7. Confidentiality

Vendor acknowledges that it may have access to Acme's confidential manufacturing data, customer information, and pricing. Vendor agrees to maintain confidentiality for a period of five (5) years post-termination and to comply with the DPDP Act, 2023 for any personal data processing.

## 8. Data Protection

Vendor shall:
(a) Process personal data only as necessary to perform obligations under this Agreement;
(b) Implement appropriate technical and organisational measures per DPDP Act Section 12;
(c) Notify Acme within seventy-two (72) hours of any personal data breach;
(d) Delete or return all personal data upon contract termination.

## 9. Termination

(a) Either Party may terminate for convenience with ninety (90) days written notice.

(b) Either Party may terminate for cause immediately upon written notice if the other Party commits a material breach and fails to cure within thirty (30) days of receiving notice.

(c) Upon termination, Vendor shall complete all work-in-progress and deliver accepted goods within thirty (30) days.

## 10. Limitation of Liability

(a) Vendor's total liability for all claims arising under this Agreement shall not exceed the total amount paid to Vendor under this Agreement in the twelve (12) months preceding the claim.

(b) Neither Party shall be liable for indirect, incidental, special, consequential, or punitive damages, including lost profits, even if advised of the possibility thereof.

(c) The limitations in this Section shall not apply to: (i) breaches of confidentiality; (ii) IP infringement; (iii) fraud or wilful misconduct; (iv) death or personal injury.

## 11. Indemnity

Vendor shall indemnify and hold harmless Acme from all claims, damages, and expenses arising from: (a) Vendor's negligence or wilful misconduct; (b) breach of this Agreement; (c) infringement of third-party IP rights.

## 12. Force Majeure

Neither Party shall be liable for failure to perform due to causes beyond its reasonable control, including but not limited to: acts of God, war, terrorism, riots, fire, flood, epidemic, government actions, or labour disputes. The affected Party shall give prompt written notice and use reasonable efforts to mitigate.

## 13. Governing Law and Dispute Resolution

(a) This Agreement shall be governed by the laws of India.

(b) Any dispute shall first be resolved through good faith negotiations between senior management.

(c) If unresolved within thirty (30) days, disputes shall be settled by arbitration in Mumbai under the Arbitration and Conciliation Act, 1996. The arbitral tribunal shall consist of one (1) arbitrator appointed mutually. The seat shall be Mumbai and the language shall be English.

(d) Each Party irrevocably submits to the exclusive jurisdiction of the courts at Mumbai.

## 14. General Provisions

(a) **Entire Agreement:** This Agreement constitutes the entire agreement and supersedes all prior understandings.
(b) **Amendment:** No amendment shall be valid unless in writing signed by both Parties.
(c) **Assignment:** Vendor shall not assign this Agreement without Acme's prior written consent.
(d) **Waiver:** No waiver shall be valid unless in writing.
(e) **Notices:** All notices shall be in writing and delivered to the addresses stated above.

## Signatures

**For Acme Manufacturing Pvt Ltd:**

Name: Vikram Rao
Title: Procurement Head
Date: 01 March 2024
Aadhaar: 4567 8901 2345

**For TechSupply Solutions Pvt Ltd:**

Name: Amit Patel
Title: Business Head
Date: 01 March 2024
PAN: AAAPA1234A
"""

EMPLOYMENT_TEXT = """# EMPLOYMENT AGREEMENT

## Date: 01 April 2024

## Parties

**Employer:** Acme Manufacturing Pvt Ltd, a company incorporated under the Companies Act, 2013, having its registered office at Plot 42, Industrial Estate, Pune, Maharashtra 411001. CIN: U29120MH2015PTC123456. GSTIN: 27AABCU9603R1ZX.

**Employee:** Rahul Verma, son of Mr. Sunil Verma, residing at Flat 302, Sunrise Apartments, Koregaon Park, Pune 411001. Date of Birth: 15 August 1990. Aadhaar: 5678 9012 3456. PAN: CDEFG5678H. UPI: rahul.verma@okaxis

## 1. Position and Duties

(a) Employer hereby employs Employee as "Senior Mechanical Engineer — Product Development."

(b) Employee shall report to the Head of Engineering and shall perform duties as may be assigned from time to time, including but not limited to: design and development of precision mechanical components, CAD modelling, prototype testing, and supplier quality coordination.

(c) Employee's work location shall be Acme's Pune facility, with occasional travel to vendor locations and client sites as required.

## 2. Term

(a) This Agreement shall commence on 01 April 2024 and continue until terminated in accordance with Section 8.

(b) The first six (6) months shall constitute a probationary period during which either Party may terminate with seven (7) days written notice.

## 3. Compensation and Benefits

(a) **Basic Salary:** INR 1,20,000 per month (Rupees One Lakh Twenty Thousand Only).

(b) **Annual CTC:** INR 24,00,000 (Rupees Twenty-Four Lakhs Only) inclusive of basic salary, HRA (40% of basic), special allowance, and employer PF contribution.

(c) **Payment:** Salary shall be credited to Employee's bank account by the 7th of each month:
   Bank: ICICI Bank
   Account: 001234567890
   IFSC: ICIC0000123

(d) **Performance Bonus:** Employee shall be eligible for an annual performance bonus of up to 20% of annual CTC, payable in April each year based on individual and company performance.

(e) **ESOPs:** Employee shall be granted 2,000 stock options vesting over four (4) years with a one (1) year cliff.

(f) **Leave:** 24 days earned leave, 12 days sick leave, 10 days casual leave per calendar year.

(g) **Insurance:** Group health insurance (sum insured INR 10,00,000), group term life insurance (sum insured INR 50,00,000), and personal accident cover.

## 4. Working Hours

(a) Employee shall work forty (40) hours per week, Monday to Friday, 9:00 AM to 6:00 PM with one hour for lunch.

(b) Employee may be required to work overtime with prior approval. Overtime shall be compensated at 1.5x the hourly rate or through compensatory off, as per the Code on Wages, 2019.

## 5. Confidentiality and Non-Disclosure

(a) Employee acknowledges that during employment, Employee will have access to confidential and proprietary information including but not limited to: product designs, manufacturing processes, customer data, pricing strategies, and business plans.

(b) Employee agrees to maintain strict confidentiality during employment and for a period of twenty-four (24) months after termination.

(c) Employee shall not remove any confidential documents, data, or materials from Employer's premises without prior written consent.

(d) Employee agrees to comply with the DPDP Act, 2023 and shall not process any personal data of customers, vendors, or employees except as authorised.

## 6. Intellectual Property Assignment

(a) All inventions, discoveries, improvements, designs, software, documents, and other work product created by Employee during working hours or using Employer's resources, facilities, or confidential information ("Work Product") shall be the sole and exclusive property of Employer.

(b) Employee hereby irrevocably assigns to Employer all rights, title, and interest in and to all Work Product, including all intellectual property rights therein.

(c) Employee shall execute all documents and provide all assistance reasonably required to perfect Employer's ownership of Work Product.

(d) This Section shall survive termination of employment.

## 7. Non-Compete and Non-Solicitation

(a) During employment and for a period of twelve (12) months after termination, Employee shall not directly or indirectly engage in any business that competes with Employer's business within India.

(b) Employee shall not solicit Employer's customers, vendors, or employees for a period of twelve (12) months after termination.

(c) Employee acknowledges that the restrictions in this Section are reasonable and necessary to protect Employer's legitimate business interests.

(d) If any restriction is found unenforceable by a court of competent jurisdiction, the Parties agree that the court shall modify the restriction to the minimum extent necessary to make it enforceable.

## 8. Termination

(a) **By Employee:** Employee may resign by providing sixty (60) days written notice or payment in lieu thereof.

(b) **By Employer for Convenience:** Employer may terminate by providing three (3) months' salary as severance or sixty (60) days written notice.

(c) **By Employer for Cause:** Employer may terminate immediately for: gross misconduct, fraud, theft, breach of confidentiality, wilful insubordination, or material breach of this Agreement.

(d) **Death or Disability:** This Agreement shall terminate upon Employee's death or permanent disability, with Employer paying statutory dues and any accrued but unpaid salary.

(e) **Return of Property:** Upon termination, Employee shall return all company property, documents, access cards, and electronic devices.

## 9. Compliance with Labour Laws

Employee and Employer agree to comply with all applicable central and state labour laws including:

(a) Code on Wages, 2019
(b) Industrial Relations Code, 2020
(c) Code on Social Security, 2020
(d) Occupational Safety, Health and Working Conditions Code, 2020
(e) Maternity Benefit Act, 1961 (as applicable)
(f) Payment of Gratuity Act, 1972
(g) Employees' Provident Funds and Miscellaneous Provisions Act, 1952

## 10. Grievance Redressal

(a) Employee may raise grievances through Employer's internal grievance mechanism.

(b) If unresolved, matters may be referred to the Labour Commissioner, Pune, under the Industrial Relations Code, 2020.

## 11. Governing Law and Jurisdiction

This Agreement shall be governed by the laws of India. Disputes shall be subject to the jurisdiction of the courts at Pune, Maharashtra.

## 12. General

(a) **Entire Agreement:** This Agreement supersedes all prior agreements.
(b) **Severability:** Invalid provisions shall be severed; remaining provisions shall continue.
(c) **Notices:** Notices shall be in writing to the addresses stated above.

## Signatures

**For Acme Manufacturing Pvt Ltd:**

Name: Anand Mehta
Title: CEO & Managing Director
Date: 01 April 2024

**Employee:**

Name: Rahul Verma
Date: 01 April 2024
Aadhaar: 5678 9012 3456
PAN: CDEFG5678H
"""

LICENSE_TEXT = """# SOFTWARE LICENSE AGREEMENT

## Date: 10 June 2024

## Parties

**Licensor:** CloudStack Technologies Pvt Ltd ("CloudStack"), CIN U72200KA2015PTC078901, GSTIN 29AABCC2345B1Z6, registered at 7th Floor, Embassy Tech Village, Outer Ring Road, Bangalore 560103, Karnataka, India. Contact: Arjun Reddy, VP Sales — arjun.reddy@cloudstack.io | +91 99876 54321 | Aadhaar: 7890 1234 5678

**Licensee:** Acme Manufacturing Pvt Ltd ("Acme"), CIN U29120MH2015PTC123456, GSTIN 27AABCU9603R1ZX, registered at Plot 42, Industrial Estate, Pune, Maharashtra 411001, India. Contact: Sneha Iyer, CTO — sneha.iyer@acmemfg.in | +91 88990 11223 | PAN: FGHIJ9012K

## 1. Definitions

(a) "Software" means CloudStack ERP Manufacturing Module v4.2, including all object code, documentation, updates, and patches.

(b) "Authorized Users" means up to fifty (50) named employees of Licensee.

(c) "Deployment" means installation on Licensee's AWS India (Mumbai) region infrastructure.

## 2. License Grant

(a) Subject to payment of License Fees and compliance with this Agreement, CloudStack hereby grants Acme a non-exclusive, non-transferable, perpetual license to use the Software for its internal business operations.

(b) The license is restricted to Deployment at the designated cloud infrastructure. Use at additional locations requires a separate addendum.

(c) Acme shall not: (i) reverse engineer, decompile, or disassemble the Software; (ii) sublicense, rent, lease, or distribute the Software; (iii) use the Software to provide services to third parties; (iv) remove any proprietary notices.

## 3. License Fees and Payment

(a) **License Fee:** INR 35,00,000 (Rupees Thirty-Five Lakhs Only) for the perpetual license, payable as follows:
   - 50% upon execution (INR 17,50,000)
   - 25% upon successful UAT (INR 8,75,000)
   - 25% upon go-live (INR 8,75,000)

(b) **Annual Maintenance:** INR 7,00,000 per annum, inclusive of updates, patches, and technical support (business hours, 9 AM–6 PM IST).

(c) **Payment Terms:** Net 30 days from invoice date. Payments via NEFT to:
   Bank: State Bank of India
   Account: 345678901234
   IFSC: SBIN0001234
   UPI: cloudstack@sbi

(d) **GST:** All amounts are exclusive of GST at applicable rates. CloudStack shall raise tax invoices with valid GSTIN.

(e) Late payments shall attract interest at 1.5% per month or the maximum rate permissible under RBI guidelines, whichever is lower.

## 4. Implementation and Support

(a) CloudStack shall commence implementation within fifteen (15) days of receipt of advance payment.

(b) Implementation shall be completed within ninety (90) days, subject to Licensee providing timely data, infrastructure access, and user availability.

(c) CloudStack shall provide: (i) project manager; (ii) two (2) technical consultants; (iii) training for up to twenty (20) users.

(d) Post go-live, CloudStack shall provide Level 2 support via ticketing system with response times: Critical (4 hours), High (8 hours), Medium (24 hours), Low (48 hours).

## 5. Data Protection and Security

(a) CloudStack shall process Licensee data only as necessary to provide the licensed services.

(b) CloudStack shall implement technical and organisational measures per DPDP Act, 2023 and ISO 27001:2022.

(c) All data shall be stored within India (AWS Mumbai region) per RBI data localisation guidelines for regulated entities.

(d) CloudStack shall maintain encryption at rest (AES-256) and in transit (TLS 1.3).

(e) CloudStack shall notify Acme within twenty-four (24) hours of any security incident or personal data breach.

(f) Upon termination, CloudStack shall export all data in standard formats (CSV, JSON, SQL dump) within thirty (30) days and securely delete all copies within ninety (90) days.

## 6. Intellectual Property

(a) CloudStack retains all rights, title, and interest in the Software, including all IP rights.

(b) Acme retains all rights to its data uploaded to the Software.

(c) Any customisations or integrations developed specifically for Acme shall be owned by Acme, provided Acme has paid all applicable fees.

## 7. Warranties

(a) CloudStack warrants that the Software shall materially conform to the functional specifications for a period of ninety (90) days from go-live.

(b) CloudStack warrants that it has the right to grant the license and that the Software does not infringe any third-party IP rights.

(c) EXCEPT AS EXPRESSLY STATED, ALL WARRANTIES ARE DISCLAIMED TO THE MAXIMUM EXTENT PERMITTED BY LAW.

## 8. Limitation of Liability

(a) CloudStack's total liability shall not exceed the total fees paid by Acme in the twelve (12) months preceding the claim.

(b) Neither Party shall be liable for indirect, consequential, or punitive damages.

(c) The limitations shall not apply to: breach of confidentiality, IP infringement, fraud, or data breach.

## 9. Term and Termination

(a) This Agreement shall commence on the Effective Date and continue unless terminated.

(b) Either Party may terminate for material breach with thirty (30) days cure notice.

(c) Acme may terminate for convenience with ninety (90) days written notice, pro-rata refund of prepaid maintenance fees.

(d) CloudStack may terminate immediately if Acme breaches license restrictions.

(e) Sections 5, 6, 8, 10, and 11 shall survive termination.

## 10. Indemnity

(a) CloudStack shall indemnify Acme against third-party IP infringement claims.

(b) Acme shall indemnify CloudStack against claims arising from Acme data or misuse of the Software.

## 11. Force Majeure

Neither Party shall be liable for failure due to events beyond reasonable control including acts of God, war, epidemic, government action, or internet outages beyond the affected Party's control.

## 12. Governing Law and Dispute Resolution

(a) This Agreement shall be governed by the laws of India.

(b) Disputes shall be resolved by arbitration in Bangalore under the Arbitration and Conciliation Act, 1996, with one (1) arbitrator. Language: English. Seat: Bangalore.

(c) Courts at Bangalore shall have exclusive jurisdiction.

## 13. General

(a) Entire Agreement; (b) No waiver without writing; (c) No assignment without consent; (d) Notices to addresses above; (e) Severability.

## Signatures

**For CloudStack Technologies Pvt Ltd:**

Name: Arjun Reddy
Title: VP Sales
Date: 10 June 2024
Aadhaar: 7890 1234 5678

**For Acme Manufacturing Pvt Ltd:**

Name: Sneha Iyer
Title: CTO
Date: 10 June 2024
PAN: FGHIJ9012K
"""


def _generate_plain_english(clause_type: str, clause_text: str) -> str:
    """Generate a simple plain-English summary of a clause."""
    summaries = {
        "termination": "This clause explains how and when the agreement can be ended by either party, including notice periods and conditions for immediate termination.",
        "liability": "This clause limits how much either party can be held financially responsible for if something goes wrong under the agreement.",
        "payment": "This clause sets out when and how payments must be made, including any late fees or interest charges for delayed payments.",
        "confidentiality": "This clause requires both parties to keep sensitive business information private and not share it with outsiders.",
        "governing_law": "This clause states which country's laws will be used to interpret the agreement and where disputes will be resolved.",
        "intellectual_property": "This clause clarifies who owns the ideas, inventions, and creative work produced during the agreement.",
        "force_majeure": "This clause excuses delays or failures caused by events beyond anyone's control, such as natural disasters or government actions.",
        "indemnity": "This clause requires one party to compensate the other for certain losses, damages, or legal claims arising from the agreement.",
        "data_processing": "This clause governs how personal data must be handled, stored, and protected in compliance with privacy laws.",
        "non_compete": "This clause restricts one party from competing with the other or poaching customers and employees for a specified period.",
    }
    base = summaries.get(clause_type, f"This clause governs {clause_type.replace('_', ' ')} matters between the parties.")
    # Add a sentence summarising the specific text
    if len(clause_text) > 100:
        base += f" Specifically: {clause_text[:200]}..."
    else:
        base += f" Specifically: {clause_text}"
    return base


async def seed_database():
    """Seed default data if not present."""
    async with async_session_factory() as session:
        # ── Org ──
        result = await session.execute(select(Organization).where(Organization.id == "demo-org"))
        if result.scalar_one_or_none() is None:
            org = Organization(
                id="demo-org",
                name="Acme Manufacturing Pvt Ltd",
                slug="acme-mfg",
                industry="manufacturing",
                revenue_range="100-300cr",
                employee_count=250,
                address="Plot 42, Industrial Estate, Pune, Maharashtra 411001",
                gstin="27AABCU9603R1ZX",
                cin="U29120MH2015PTC123456",
                dpo_name="Rajesh Sharma",
                dpo_email="dpo@acmemfg.in",
            )
            session.add(org)

        # ── Playbook Rules (real company standards) ──
        # Always clear and re-seed to ensure latest rule scopes are active
        from sqlalchemy import delete
        await session.execute(delete(PlaybookRule).where(PlaybookRule.org_id == "demo-org"))
        rules = [
            # ── Universal rules ──
            PlaybookRule(org_id="demo-org", rule_name="Min Termination Notice — 30 Days", rule_type="termination",
                         condition="min_value", threshold_value="30", severity="critical"),
            PlaybookRule(org_id="demo-org", rule_name="Indian Governing Law Mandatory", rule_type="governing_law",
                         condition="must_have", threshold_value="yes", severity="critical"),
            PlaybookRule(org_id="demo-org", rule_name="DPDP Consent Language Required", rule_type="data_processing",
                         condition="must_have", threshold_value="yes", severity="high"),
            PlaybookRule(org_id="demo-org", rule_name="Arbitration Seat — India Preferred", rule_type="dispute_resolution",
                         condition="must_have", threshold_value="india", severity="medium"),
            # ── NDA-specific ──
            PlaybookRule(org_id="demo-org", rule_name="NDA: Mutual NDA Clause Required", rule_type="confidentiality",
                         condition="must_have", threshold_value="mutual", severity="critical", contract_type="nda"),
            PlaybookRule(org_id="demo-org", rule_name="NDA: Return Period ≤ 15 Days", rule_type="termination",
                         condition="max_value", threshold_value="15", severity="high", contract_type="nda"),
            PlaybookRule(org_id="demo-org", rule_name="NDA: Survival Period ≥ 2 Years", rule_type="confidentiality",
                         condition="min_value", threshold_value="24", severity="high", contract_type="nda"),
            # ── Employment-specific ──
            PlaybookRule(org_id="demo-org", rule_name="Employment: IP Assignment Clause Required", rule_type="intellectual_property",
                         condition="must_have", threshold_value="explicit", severity="critical", contract_type="employment"),
            PlaybookRule(org_id="demo-org", rule_name="Employment: Non-Compete ≤ 12 Months", rule_type="non_compete",
                         condition="max_value", threshold_value="12", severity="high", contract_type="employment"),
            PlaybookRule(org_id="demo-org", rule_name="Employment: Probation Period ≤ 6 Months", rule_type="termination",
                         condition="max_value", threshold_value="180", severity="medium", contract_type="employment"),
            PlaybookRule(org_id="demo-org", rule_name="Employment: Gratuity Reference Required", rule_type="payment",
                         condition="must_have", threshold_value="gratuity", severity="high", contract_type="employment"),
            PlaybookRule(org_id="demo-org", rule_name="Employment: Background Check Required", rule_type="confidentiality",
                         condition="must_have", threshold_value="background_check", severity="medium", contract_type="employment"),
            # ── Vendor-specific ──
            PlaybookRule(org_id="demo-org", rule_name="Vendor: Liability Cap ≤ 2x Annual Value", rule_type="liability",
                         condition="max_value", threshold_value="10000000", severity="high", contract_type="vendor"),
            PlaybookRule(org_id="demo-org", rule_name="Vendor: Payment Terms ≤ 30 Days", rule_type="payment",
                         condition="max_value", threshold_value="30", severity="medium", contract_type="vendor"),
            PlaybookRule(org_id="demo-org", rule_name="Vendor: Insurance Certificate Required", rule_type="indemnity",
                         condition="must_have", threshold_value="insurance", severity="high", contract_type="vendor"),
            PlaybookRule(org_id="demo-org", rule_name="Vendor: SLA Clause Required", rule_type="warranty",
                         condition="must_have", threshold_value="sla", severity="medium", contract_type="vendor"),
            PlaybookRule(org_id="demo-org", rule_name="Vendor: Auto-Renewal Clause Required", rule_type="termination",
                         condition="must_have", threshold_value="explicit_clause", severity="high", contract_type="vendor"),
            PlaybookRule(org_id="demo-org", rule_name="Vendor: Force Majeure — Specific Events List", rule_type="force_majeure",
                         condition="must_have", threshold_value="explicit_list", severity="medium", contract_type="vendor"),
            # ── License-specific ──
            PlaybookRule(org_id="demo-org", rule_name="License: Data Localisation Clause Required", rule_type="data_processing",
                         condition="must_have", threshold_value="india_storage", severity="critical", contract_type="license"),
            PlaybookRule(org_id="demo-org", rule_name="License: Warranty Period ≥ 90 Days", rule_type="warranty",
                         condition="min_value", threshold_value="90", severity="high", contract_type="license"),
            PlaybookRule(org_id="demo-org", rule_name="License: UAT Milestone Required", rule_type="termination",
                         condition="must_have", threshold_value="uat", severity="medium", contract_type="license"),
            PlaybookRule(org_id="demo-org", rule_name="License: Exit Clause (Data Export) Required", rule_type="data_processing",
                         condition="must_have", threshold_value="exit_clause", severity="high", contract_type="license"),
        ]
        for r in rules:
            session.add(r)

        # ── Enforceability Benchmarks (real Indian law) ──
        result = await session.execute(select(EnforceabilityBenchmark))
        if not result.scalars().all():
            benchmarks = [
                EnforceabilityBenchmark(clause_type="termination", statute_act="Indian Contract Act, 1872",
                    section_number="Section 56", enforceability_score=0.92, conditions="Must be explicit and reasonable. Doctrine of frustration applies only to impossibility, not mere inconvenience."),
                EnforceabilityBenchmark(clause_type="liability", statute_act="Indian Contract Act, 1872",
                    section_number="Section 73", enforceability_score=0.88, conditions="Genuine pre-estimate of loss required. Penalty clauses may be reduced by courts per Section 74."),
                EnforceabilityBenchmark(clause_type="data_processing", statute_act="Digital Personal Data Protection Act, 2023",
                    section_number="Section 12", enforceability_score=0.95, conditions="Consent must be free, specific, informed, unconditional, and unambiguous with clear affirmative action."),
                EnforceabilityBenchmark(clause_type="governing_law", statute_act="Indian Contract Act, 1872",
                    section_number="Section 10", enforceability_score=0.97, conditions="Must be a lawful agreement with competent parties, free consent, lawful consideration, and lawful object."),
                EnforceabilityBenchmark(clause_type="payment", statute_act="Indian Contract Act, 1872",
                    section_number="Section 10", enforceability_score=0.85, conditions="Clear payment terms enforceable. Interest on delayed payments governed by MSMED Act if applicable."),
                EnforceabilityBenchmark(clause_type="confidentiality", statute_act="Indian Contract Act, 1872",
                    section_number="Section 27", enforceability_score=0.72, conditions="Must not be overly broad in restraint of trade. Reasonable territorial and temporal limits required."),
                EnforceabilityBenchmark(clause_type="indemnity", statute_act="Indian Contract Act, 1872",
                    section_number="Section 124", enforceability_score=0.90, conditions="Must define scope of indemnity clearly. Cannot extend to consequences of indemnifier's own negligence unless explicit."),
                EnforceabilityBenchmark(clause_type="force_majeure", statute_act="Indian Contract Act, 1872",
                    section_number="Section 56", enforceability_score=0.93, conditions="Must list specific events. Blanket force majeure clauses may be interpreted narrowly by Indian courts."),
                EnforceabilityBenchmark(clause_type="warranty", statute_act="Consumer Protection Act, 2019",
                    section_number="Section 2(39)", enforceability_score=0.87, conditions="Must not exclude statutory rights. Unfair contract terms may be void per Section 49."),
                EnforceabilityBenchmark(clause_type="dispute_resolution", statute_act="Arbitration and Conciliation Act, 1996",
                    section_number="Section 7", enforceability_score=0.91, conditions="Arbitration agreement must be in writing. Unilateral appointment clauses struck down per Perkins judgment."),
                EnforceabilityBenchmark(clause_type="non_compete", statute_act="Indian Contract Act, 1872",
                    section_number="Section 27", enforceability_score=0.68, conditions="Generally void except in sale of goodwill. Post-employment non-compete unenforceable unless protecting trade secrets with reasonable limits."),
                EnforceabilityBenchmark(clause_type="intellectual_property", statute_act="Copyright Act, 1957",
                    section_number="Section 17", enforceability_score=0.94, conditions="Work made in course of employment vests in employer. Must be express assignment for future works."),
                EnforceabilityBenchmark(clause_type="confidentiality", statute_act="Digital Personal Data Protection Act, 2023",
                    section_number="Section 5(1)", enforceability_score=0.93, conditions="Principle of purpose limitation. Personal data must be used only for specified, explicit, and legitimate purposes."),
                EnforceabilityBenchmark(clause_type="confidentiality", statute_act="Indian Contract Act, 1872",
                    section_number="Section 27 Exception 2", enforceability_score=0.75, conditions="Trade secret protection may justify reasonable non-compete. Must be limited in time, geography, and scope."),
                EnforceabilityBenchmark(clause_type="payment", statute_act="Code on Wages, 2019",
                    section_number="Section 17", enforceability_score=0.88, conditions="Wages must be paid within prescribed time. Deductions limited to 50% of total wages."),
                EnforceabilityBenchmark(clause_type="intellectual_property", statute_act="Patents Act, 1970",
                    section_number="Section 39", enforceability_score=0.82, conditions="Inventions made during employment may belong to employer if contractually assigned. Must be specific."),
                EnforceabilityBenchmark(clause_type="warranty", statute_act="Sale of Goods Act, 1930",
                    section_number="Section 16", enforceability_score=0.86, conditions="Implied conditions as to quality and fitness. Exclusion clauses must be explicit and brought to buyer's notice."),
                EnforceabilityBenchmark(clause_type="assignment", statute_act="Indian Contract Act, 1872",
                    section_number="Section 37", enforceability_score=0.89, conditions="Assignment must be absolute and not by way of charge only. Notice to obligor required for legal effect."),
                EnforceabilityBenchmark(clause_type="data_processing", statute_act="Information Technology Act, 2000",
                    section_number="Section 43A", enforceability_score=0.82, conditions="Reasonable security practices required. Compensation for failure to protect sensitive personal data."),
                EnforceabilityBenchmark(clause_type="liability", statute_act="Companies Act, 2013",
                    section_number="Section 166", enforceability_score=0.79, conditions="Director liability caps may not protect against fraud, negligence, or breach of fiduciary duty."),
                EnforceabilityBenchmark(clause_type="payment", statute_act="Micro, Small and Medium Enterprises Development Act, 2006",
                    section_number="Section 16", enforceability_score=0.96, conditions="Payment to MSME vendor must be within 45 days. Compound interest at 3x RBI rate for delayed payments. Mandatory."),
                EnforceabilityBenchmark(clause_type="termination", statute_act="Industrial Relations Code, 2020",
                    section_number="Section 67", enforceability_score=0.85, conditions="Retrenchment compensation mandatory for workmen. 15 days average pay per completed year of service."),
                EnforceabilityBenchmark(clause_type="confidentiality", statute_act="Digital Personal Data Protection Act, 2023",
                    section_number="Section 8", enforceability_score=0.90, conditions="Data fiduciary must ensure completeness, accuracy, and consistency of personal data. Breach notification within 72 hours."),
                # Low-score benchmarks to ensure law layer produces findings in demo
                EnforceabilityBenchmark(clause_type="payment", statute_act="Micro, Small and Medium Enterprises Development Act, 2006",
                    section_number="Section 16", enforceability_score=0.35, conditions="Payment to MSME vendor must be within 45 days. Compound interest at 3x RBI rate for delayed payments. Many contracts fail to specify the 45-day ceiling explicitly."),
                EnforceabilityBenchmark(clause_type="non_compete", statute_act="Indian Contract Act, 1872",
                    section_number="Section 27", enforceability_score=0.30, conditions="Post-employment non-compete clauses are generally void in India. Only enforceable when protecting trade secrets with strictly reasonable geographic and temporal limits."),
                EnforceabilityBenchmark(clause_type="data_processing", statute_act="Reserve Bank of India Master Direction",
                    section_number="Section 6", enforceability_score=0.40, conditions="Financial data must be stored exclusively in India. Cross-border flow permitted only under explicit RBI approval. Most SaaS contracts lack explicit localisation clause."),
            ]
            for b in benchmarks:
                session.add(b)

        # ── Regulatory Updates (real Indian regulatory landscape) ──
        result = await session.execute(select(RegulatoryUpdate).where(RegulatoryUpdate.id == "upd-dpdp-2025"))
        if result.scalar_one_or_none() is None:
            updates = [
                RegulatoryUpdate(id="upd-dpdp-2025", source_id="dpdp", title="DPDP Act 2023: Compliance Framework Released by MeitY",
                    summary="Ministry of Electronics and IT released the DPDP Compliance Framework on 15 March 2025. All data fiduciaries must appoint Data Protection Officer, conduct DPIA for high-risk processing, and implement consent management platforms by 31 December 2026.",
                    effective_date="2025-03-15", affected_clause_types=["data_processing", "confidentiality"]),
                RegulatoryUpdate(id="upd-labour-2025", source_id="labour", title="4 Labour Codes: Central Rules Notified Effective November 2025",
                    summary="Ministry of Labour and Employment notified central rules under all four Labour Codes. Key changes: single licence for contractors, digital labour registers, fixed-term employment formalised, and social security portability via Universal Account Number.",
                    effective_date="2025-11-01", affected_clause_types=["termination", "payment", "confidentiality"]),
                RegulatoryUpdate(id="upd-rbi-2025", source_id="rbi", title="RBI Master Direction on Outsourcing: Enhanced Data Localisation",
                    summary="RBI issued revised Master Direction on Information Technology Framework for NBFCs and banks. All customer data must remain within Indian jurisdiction. Cross-border data transfer only to jurisdictions with adequacy decisions or with explicit RBI approval.",
                    effective_date="2025-04-01", affected_clause_types=["data_processing", "governing_law", "liability"]),
                RegulatoryUpdate(id="upd-sebi-2025", source_id="sebi", title="SEBI LODR (Amendment) Regulations 2025: ESG Disclosure Mandate",
                    summary="SEBI mandated BRSR Core disclosures for top 1,000 listed companies from FY 2025-26. Supply chain ESG due diligence, carbon footprint reporting, and gender pay gap disclosures now mandatory in annual reports.",
                    effective_date="2025-06-01", affected_clause_types=["confidentiality", "data_processing", "warranty"]),
                RegulatoryUpdate(id="upd-mca-2025", source_id="mca", title="MCA Introduces SPICe+ Part B for LLP Conversion and Dormancy",
                    summary="Ministry of Corporate Affairs introduced simplified forms for LLP conversion and dormant company status. Form CHG-1 revamped for charge creation/modification. Mandatory e-AGM guidelines updated for FY 2025-26.",
                    effective_date="2025-07-14", affected_clause_types=["governing_law", "assignment", "termination"]),
                RegulatoryUpdate(id="upd-gst-2025", source_id="gst", title="GST Council 55th Meeting: Reverse Charge on IT Services Extended",
                    summary="GST Council decided to extend reverse charge mechanism on IT and consultancy services by unregistered persons to registered persons. E-invoicing threshold reduced to INR 5 crore from 1 April 2026.",
                    effective_date="2025-08-01", affected_clause_types=["payment", "liability"]),
                RegulatoryUpdate(id="upd-epfo-2025", source_id="labour", title="EPFO Circular: Higher Pension Scheme Opt-in Deadline Extended",
                    summary="Employees' Provident Fund Organisation extended the opt-in deadline for higher pension under EPS-95 to 30 June 2025. Employers must reconcile contribution records and submit joint option forms digitally.",
                    effective_date="2025-05-15", affected_clause_types=["payment", "termination"]),
                RegulatoryUpdate(id="upd-competition-2025", source_id="mca", title="CCI (General) Regulations 2025: Leniency Plus Programme",
                    summary="Competition Commission of India introduced Leniency Plus for cartel members who expose other cartels. Penalty reduction up to 100% for first applicant. Digital markets gatekeeper obligations expanded.",
                    effective_date="2025-09-01", affected_clause_types=["governing_law", "liability", "indemnity"]),
                RegulatoryUpdate(id="upd-it-2025", source_id="mca", title="Income Tax (24th Amendment) Rules 2025: TDS on Crypto Assets",
                    summary="CBDT notified 1% TDS on transfer of virtual digital assets above INR 50,000 per annum. Crypto exchanges must report transactions to IT Department. PAN-Aadhaar linkage deadline extended to 31 March 2026.",
                    effective_date="2025-07-01", affected_clause_types=["payment", "liability"]),
                RegulatoryUpdate(id="upd-ibbi-2025", source_id="rbi", title="IBBI Circular: Pre-packaged Insolvency Resolution Process Expanded to MSMEs",
                    summary="Insolvency and Bankruptcy Board of India expanded PP-IRP to all MSMEs with default above INR 10 lakh. Debtor-in-possession model with 90-day resolution timeline. Moratorium limited to 120 days.",
                    effective_date="2025-06-15", affected_clause_types=["termination", "payment", "liability"]),
            ]
            for u in updates:
                session.add(u)

        # ── Regulatory Alerts ──
        result = await session.execute(select(RegulatoryAlert).where(RegulatoryAlert.org_id == "demo-org"))
        if not result.scalars().all():
            alerts = [
                RegulatoryAlert(id="alert-1", org_id="demo-org", update_id="upd-dpdp-2025",
                    title="DPDP Act: DPO Appointment & DPIA Mandatory by Dec 2026",
                    description="Your contracts processing employee/customer personal data must include DPDP Section 12 compliant consent language. Review all vendor agreements with data processing clauses.",
                    priority="critical", affected_contract_ids=["demo-c1", "demo-c4"], suggested_actions=["Add DPDP consent addendum to all active contracts", "Appoint Data Protection Officer", "Conduct DPIA for HR data processing"]),
                RegulatoryAlert(id="alert-2", org_id="demo-org", update_id="upd-labour-2025",
                    title="4 Labour Codes: Employment Contracts Need Clause Updates by Nov 2025",
                    description="New labour codes replace 29 central laws. Your employment contract with Rahul Verma requires updated termination, payment, and social security clauses.",
                    priority="high", affected_contract_ids=["demo-c3"], suggested_actions=["Update termination notice to comply with IRC 2020", "Revise gratuity calculation", "Add social security portability clause"]),
                RegulatoryAlert(id="alert-3", org_id="demo-org", update_id="upd-rbi-2025",
                    title="RBI Master Direction: Cloud Software Agreements Need Data Localisation Clause",
                    description="Your Software License Agreement with CloudStack Technologies must explicitly require India-only data storage per RBI Master Direction on Outsourcing.",
                    priority="high", affected_contract_ids=["demo-c4"], suggested_actions=["Add India data localisation clause", "Require RBI compliance certification from vendor", "Review AWS region restrictions"]),
                RegulatoryAlert(id="alert-4", org_id="demo-org", update_id="upd-sebi-2025",
                    title="SEBI LODR: ESG Due Diligence Required in Vendor Contracts",
                    description="If Acme has any listed customers or subsidiaries, vendor contracts must include ESG reporting obligations and carbon disclosure requirements.",
                    priority="medium", affected_contract_ids=["demo-c1", "demo-c2"], suggested_actions=["Add ESG compliance clause to vendor agreements", "Require BRSR Core disclosure from key suppliers"]),
                RegulatoryAlert(id="alert-5", org_id="demo-org", update_id="upd-gst-2025",
                    title="GST Council: Reverse Charge on IT Services — Review Payment Clauses",
                    description="Vendor agreements for IT/consultancy services may now attract reverse charge GST. Ensure your vendor agreements clearly specify GST liability.",
                    priority="medium", affected_contract_ids=["demo-c4"], suggested_actions=["Clarify GST liability in software license", "Update invoicing templates for RCM"]),
                RegulatoryAlert(id="alert-6", org_id="demo-org", update_id="upd-ibbi-2025",
                    title="IBBI: MSME Insolvency Rules Affect Payment Terms in Vendor Agreements",
                    description="New pre-packaged insolvency rules for MSMEs with defaults above INR 10 lakh may affect your vendor TechSupply Solutions. Review payment security mechanisms.",
                    priority="low", affected_contract_ids=["demo-c2"], suggested_actions=["Review vendor creditworthiness", "Add escrow for large payments", "Consider bank guarantee"]),
                RegulatoryAlert(id="alert-7", org_id="demo-org", update_id="upd-mca-2025",
                    title="MCA V3: Annual Filing Deadline Approaching — Compliance Obligation",
                    description="Annual Return (Form MGT-7) and Financial Statements (Form AOC-4) must be filed by 30 September 2025. Contractual compliance obligations triggered.",
                    priority="medium", affected_contract_ids=[], suggested_actions=["File MCA annual returns", "Update compliance calendar", "Notify board of directors"]),
                RegulatoryAlert(id="alert-8", org_id="demo-org", update_id="upd-epfo-2025",
                    title="EPFO: Higher Pension Opt-in Deadline 30 June 2025",
                    description="Employees eligible for higher pension under EPS-95 must submit joint option forms. HR contractual obligations require employer cooperation.",
                    priority="medium", affected_contract_ids=["demo-c3"], suggested_actions=["Communicate opt-in deadline to eligible employees", "Reconcile contribution records", "Submit joint option forms"]),
            ]
            for a in alerts:
                session.add(a)

        # ── Contract Templates ──
        result = await session.execute(select(ContractTemplate).where(ContractTemplate.org_id == "demo-org"))
        if not result.scalars().all():
            templates = [
                ContractTemplate(org_id="demo-org", name="Vendor Agreement — Manufacturing Supplies",
                    category="vendor", content="VENDOR SUPPLY AGREEMENT\n\n1. Parties: [Vendor Name] (GSTIN: [Vendor GSTIN]) and Acme Manufacturing Pvt Ltd (GSTIN: 27AABCU9603R1ZX)\n2. Scope: Supply of [Product Description] as per Schedule A\n3. Term: [Start Date] to [End Date], auto-renewal unless 90 days notice\n4. Payment: Net 30 days from valid tax invoice. Late interest 1.5% per month.\n5. Liability Cap: 2x annual contract value. Exclusions: fraud, IP breach, confidentiality.\n6. Governing Law: Laws of India. Arbitration in Mumbai under Arbitration Act, 1996.\n7. Termination: 90 days convenience; 30 days cure for cause\n8. Data Processing: DPDP Act 2023 compliance. India data storage. 72-hour breach notification.\n9. Force Majeure: Specific events listed. 30-day suspension max.\n10. Indemnity: Mutual, capped at 1x annual fees.\n\nSIGNATURES: _____________", variables={"vendor_name": "", "vendor_gstin": "", "product": "", "start_date": "", "end_date": "", "annual_value": ""}),
                ContractTemplate(org_id="demo-org", name="Employment Contract — Engineering",
                    category="employment", content="EMPLOYMENT AGREEMENT\n\n1. Employee: [Employee Name] (Aadhaar: [Aadhaar], PAN: [PAN])\n2. Position: [Job Title] reporting to [Manager]\n3. Start Date: [Date]. Probation: 6 months.\n4. Compensation: INR [Annual CTC] per annum (Basic + HRA + Special Allowance + PF)\n5. Notice Period: 60 days or payment in lieu\n6. Confidentiality: 24 months post-employment. DPDP Act compliance.\n7. IP Assignment: All work product belongs to company per Copyright Act, 1957 Section 17.\n8. Non-Compete: 12 months post-employment, India only, reasonable scope.\n9. Compliance: Code on Wages 2019, Labour Codes 2020, EPF Act 1952, Gratuity Act 1972.\n10. Grievance: Internal mechanism → Labour Commissioner Pune.\n\nSIGNATURES: _____________", variables={"employee_name": "", "aadhaar": "", "pan": "", "job_title": "", "manager": "", "start_date": "", "annual_ctc": ""}),
                ContractTemplate(org_id="demo-org", name="Mutual NDA — Third Party Collaboration",
                    category="nda", content="NON-DISCLOSURE AGREEMENT\n\n1. Parties: Acme Manufacturing Pvt Ltd and [Counterparty]\n2. Purpose: Evaluation of [Business Purpose]\n3. Confidential Information: Technical data, business plans, customer lists, pricing, personal data\n4. Obligations: Strict confidence; no third-party disclosure; DPDP Section 12 consent for personal data\n5. Term: 3 years from execution\n6. Return: All materials within 15 days of termination\n7. Remedies: Injunctive relief + indemnity\n8. Governing Law: Laws of India. Courts at Mumbai.\n9. Independent Contractors: No partnership created\n10. Severability: Invalid provisions severed; remainder continues\n\nSIGNATURES: _____________", variables={"counterparty": "", "business_purpose": ""}),
                ContractTemplate(org_id="demo-org", name="Software License — Enterprise SaaS",
                    category="license", content="SOFTWARE LICENSE AGREEMENT\n\n1. Licensor: [Vendor] and Licensee: Acme Manufacturing Pvt Ltd\n2. Software: [Product Name] v[Version]\n3. License: Non-exclusive, non-transferable, perpetual, [User Count] named users\n4. Fees: INR [License Fee] + INR [Annual AMC] maintenance\n5. Payment: Net 30. GST extra.\n6. Data: India storage only (AWS Mumbai). AES-256 encryption. TLS 1.3.\n7. DPDP: Consent management. 72-hour breach notification. Data deletion within 90 days post-termination.\n8. IP: Licensor retains all rights. Licensee owns its data.\n9. Warranty: 90-day conformity warranty. No other warranties.\n10. Liability: Cap = 12 months fees. No indirect damages.\n11. Termination: 90 days convenience. 30 days cure for breach.\n12. Arbitration: Bangalore seat. English language. One arbitrator.\n\nSIGNATURES: _____________", variables={"vendor": "", "product": "", "version": "", "user_count": "", "license_fee": "", "annual_amc": ""}),
            ]
            for t in templates:
                session.add(t)

        # ── Demo Contracts (FULL parsed_text) ──
        result = await session.execute(select(Contract).where(Contract.org_id == "demo-org"))
        if not result.scalars().all():
            await _seed_demo_contracts(session)

        # ── Obligations ──
        result = await session.execute(select(Obligation).where(Obligation.org_id == "demo-org"))
        if not result.scalars().all():
            obligations = [
                Obligation(id="ob-1", contract_id="demo-c1", org_id="demo-org",
                    description="Submit quarterly performance report to TechSupply Solutions (Q2 FY2026)",
                    obligation_type="reporting", due_date="2025-09-30", status="pending"),
                Obligation(id="ob-2", contract_id="demo-c1", org_id="demo-org",
                    description="Renew Vendor Insurance Certificate (TechSupply) — Public Liability Cover",
                    obligation_type="compliance", due_date="2025-07-15", status="pending"),
                Obligation(id="ob-3", contract_id="demo-c2", org_id="demo-org",
                    description="Quarterly GST Filing — Q1 FY2026 (GSTR-1 & GSTR-3B)",
                    obligation_type="reporting", due_date="2025-07-20", status="completed"),
                Obligation(id="ob-4", contract_id="demo-c4", org_id="demo-org",
                    description="DPDP Compliance Audit — CloudStack Data Processing Assessment",
                    obligation_type="compliance", due_date="2025-12-31", status="pending"),
                Obligation(id="ob-5", contract_id="demo-c3", org_id="demo-org",
                    description="Annual Performance Review — Rahul Verma (Senior Engineer)",
                    obligation_type="reporting", due_date="2025-04-01", status="pending"),
                Obligation(id="ob-6", contract_id="", org_id="demo-org",
                    description="File MCA Annual Return (Form MGT-7) for FY2025-26",
                    obligation_type="compliance", due_date="2025-09-30", status="pending"),
                Obligation(id="ob-7", contract_id="", org_id="demo-org",
                    description="Renew ISO 9001:2015 Certification — Surveillance Audit",
                    obligation_type="compliance", due_date="2025-06-15", status="pending"),
                Obligation(id="ob-8", contract_id="demo-c4", org_id="demo-org",
                    description="CloudStack ERP — UAT Sign-off and Go-Live Milestone",
                    obligation_type="compliance", due_date="2025-09-10", status="pending"),
            ]
            for ob in obligations:
                session.add(ob)

        # ── Automation Logs ──
        result = await session.execute(select(AutomationLog).where(AutomationLog.org_id == "demo-org"))
        if not result.scalars().all():
            logs = [
                AutomationLog(id="log-1", org_id="demo-org", automation_type="contract_upload",
                    status="completed", input_summary="NDA_InnoTech_15Jan2025.pdf", output_summary="PII: 4 entities found (2 Aadhaar, 2 PAN). Structure: 12 sections indexed. Embeddings: 8 clauses.", duration_ms=8200),
                AutomationLog(id="log-2", org_id="demo-org", automation_type="risk_assessment",
                    status="completed", input_summary="Vendor Agreement TechSupply", output_summary="Risk Score: 72/100. 3 findings: 1 critical (termination), 1 high (DPDP), 1 medium (liability).", duration_ms=3400),
                AutomationLog(id="log-3", org_id="demo-org", automation_type="regulatory_scan",
                    status="completed", input_summary="20 sources scanned (RBI, SEBI, MCA, Labour, DPDP)", output_summary="8 new alerts generated. 3 critical, 2 high, 3 medium.", duration_ms=5600),
                AutomationLog(id="log-4", org_id="demo-org", automation_type="contract_upload",
                    status="completed", input_summary="Employment_RahulVerma_01Apr2024.pdf", output_summary="PII: 3 entities found (1 Aadhaar, 1 PAN, 1 UPI). Structure: 12 sections. Embeddings: 11 clauses.", duration_ms=7800),
                AutomationLog(id="log-5", org_id="demo-org", automation_type="contract_upload",
                    status="completed", input_summary="SoftwareLicense_CloudStack_10Jun2024.pdf", output_summary="PII: 2 entities found. Structure: 13 sections. Embeddings: 12 clauses.", duration_ms=9100),
            ]
            for log in logs:
                session.add(log)

        # ── Audit Trail Entries ──
        result = await session.execute(select(AuditTrailEntry).where(AuditTrailEntry.org_id == "demo-org"))
        if not result.scalars().all():
            from app.services.audit_service import audit_service
            # Seed realistic audit entries for demo contracts
            audit_entries = [
                ("demo-c1", "CONTRACT_CREATED", "contract", "demo-c1",
                 {"title": "Mutual NDA — InnoTech Solutions Pvt Ltd", "contract_type": "nda", "source": "seed"}),
                ("demo-c1", "CLAUSES_EXTRACTED", "contract", "demo-c1",
                 {"clause_count": 5, "extracted_by": "seed", "types": ["confidentiality", "termination", "data_processing", "governing_law", "liability"]}),
                ("demo-c1", "PLAYBOOK_EVALUATED", "contract", "demo-c1",
                 {"score": 85, "violations": 1, "severity": "medium"}),
                ("demo-c2", "CONTRACT_CREATED", "contract", "demo-c2",
                 {"title": "Vendor Supply Agreement — TechSupply Solutions Pvt Ltd", "contract_type": "vendor", "source": "seed"}),
                ("demo-c2", "CLAUSES_EXTRACTED", "contract", "demo-c2",
                 {"clause_count": 8, "extracted_by": "seed", "types": ["termination", "liability", "payment", "data_processing", "confidentiality", "governing_law", "indemnity", "force_majeure"]}),
                ("demo-c2", "PLAYBOOK_EVALUATED", "contract", "demo-c2",
                 {"score": 70, "violations": 3, "severity": "high"}),
                ("demo-c3", "CONTRACT_CREATED", "contract", "demo-c3",
                 {"title": "Employment Agreement — Rahul Verma", "contract_type": "employment", "source": "seed"}),
                ("demo-c3", "CLAUSES_EXTRACTED", "contract", "demo-c3",
                 {"clause_count": 6, "extracted_by": "seed", "types": ["termination", "confidentiality", "payment", "governing_law", "intellectual_property", "non_compete"]}),
                ("demo-c3", "PLAYBOOK_EVALUATED", "contract", "demo-c3",
                 {"score": 75, "violations": 2, "severity": "medium"}),
                ("demo-c4", "CONTRACT_CREATED", "contract", "demo-c4",
                 {"title": "Software License Agreement — CloudStack Technologies Pvt Ltd", "contract_type": "license", "source": "seed"}),
                ("demo-c4", "CLAUSES_EXTRACTED", "contract", "demo-c4",
                 {"clause_count": 8, "extracted_by": "seed", "types": ["termination", "liability", "payment", "data_processing", "confidentiality", "governing_law", "intellectual_property", "force_majeure"]}),
                ("demo-c4", "PLAYBOOK_EVALUATED", "contract", "demo-c4",
                 {"score": 65, "violations": 4, "severity": "critical"}),
            ]
            for resource_id, action, resource_type, contract_id, details in audit_entries:
                await audit_service.log_action(
                    session=session,
                    org_id="demo-org",
                    actor_id="system",
                    actor_email="system@rexi.local",
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    details=details,
                )

        await session.commit()

    # ── Neo4j (fire and forget) ──
    try:
        kg_service.seed_statutes()
        kg_service.seed_regulations()
    except Exception:
        pass


async def _seed_demo_contracts(session):
    """Seed 4 realistic contracts with FULL parsed_text, clauses, risks, obligations."""
    from app.core.pdf_generator import generate_contract_pdf
    contracts_data = [
        {
            "id": "demo-c1",
            "title": "Mutual NDA — InnoTech Solutions Pvt Ltd",
            "contract_type": "nda",
            "status": "signed",
            "counterparty_name": "InnoTech Solutions Pvt Ltd",
            "counterparty_email": "priya.nair@innotech.in",
            "value_inr": 0,
            "risk_score": 0.42,
            "start_date": "2025-01-15",
            "end_date": "2028-01-14",
            "auto_renewal": False,
            "governing_law": "Laws of India",
            "parsed_text": NDA_TEXT,
            "clauses": [
                ("confidentiality", "Each party agrees to keep confidential all proprietary information disclosed during the term. Obligations survive 24 months post-termination.", 0.92),
                ("termination", "This Agreement shall commence on 15 January 2025 and remain in effect for three (3) years. Either party may terminate with thirty (30) days written notice.", 0.88),
                ("data_processing", "Vendor may process personal data as necessary to perform services. Must comply with DPDP Act, 2023 Section 12 consent requirements.", 0.75),
                ("governing_law", "This Agreement shall be governed by and construed in accordance with the laws of India. Courts at Mumbai shall have exclusive jurisdiction.", 0.96),
                ("liability", "Neither party shall be liable for indirect, consequential, or punitive damages. Total liability capped at INR 10,00,000.", 0.82),
            ],
            "findings": [
                ("medium", "termination", "Termination notice of 30 days is adequate but lacks explicit cure period for breach of confidentiality.", "Add 15-day cure period for confidentiality breaches before termination."),
                ("medium", "data_processing", "DPDP Act compliance mentioned but lacks explicit data breach notification timeline to counterparties.", "Add 72-hour breach notification clause per DPDP Section 8."),
            ],
            "obligations": [
                ("Annual NDA compliance review — verify no unauthorised disclosures", "compliance", "2025-12-31", "pending"),
            ],
            "comments": [
                ("Priya Nair", "counterparty", "NDA executed. Ready to commence technical discussions under Clause 1."),
                ("Legal Team", "reviewer", "Standard mutual NDA template used. No deviations from playbook."),
            ],
        },
        {
            "id": "demo-c2",
            "title": "Vendor Supply Agreement — TechSupply Solutions Pvt Ltd",
            "contract_type": "vendor",
            "status": "active",
            "counterparty_name": "TechSupply Solutions Pvt Ltd",
            "counterparty_email": "amit.patel@techsupply.in",
            "value_inr": 5_000_000,
            "risk_score": 0.72,
            "start_date": "2024-03-01",
            "end_date": "2026-02-28",
            "auto_renewal": True,
            "governing_law": "Laws of India",
            "parsed_text": VENDOR_TEXT,
            "clauses": [
                ("termination", "Either Party may terminate for convenience with ninety (90) days written notice. For cause: thirty (30) days cure period.", 0.88),
                ("liability", "Vendor's total liability shall not exceed total amount paid in preceding 12 months. Exclusions: fraud, IP breach, confidentiality.", 0.78),
                ("payment", "Payment terms are Net 45 days from date of invoice. Late interest 1.5% per month.", 0.72),
                ("data_processing", "Vendor may process personal data as necessary. Must comply with DPDP Act 2023. India data storage mandatory.", 0.68),
                ("confidentiality", "Each party agrees to keep confidential all proprietary information. Five (5) year post-termination obligation.", 0.85),
                ("governing_law", "This agreement shall be governed by the laws of India. Arbitration in Mumbai under Arbitration Act, 1996.", 0.94),
                ("indemnity", "Vendor indemnifies Acme for losses from negligence, breach, or IP infringement. No monetary cap specified.", 0.70),
                ("force_majeure", "Neither party liable for acts of God, war, terrorism, epidemic, government action. Prompt notice required.", 0.88),
            ],
            "findings": [
                ("critical", "termination", "Termination notice of 90 days exceeds company playbook standard of 30 days for convenience termination.", "Reduce convenience termination to 60 days or add early termination fee."),
                ("high", "payment", "Net 45 days exceeds company playbook maximum of 30 days. Cash flow impact estimated at INR 6.25L annually.", "Renegotiate to Net 30 or add 2% early payment discount."),
                ("high", "liability", "Liability cap equals 12-month fees but unlimited for fraud/IP. Indemnity clause lacks reciprocal cap.", "Add indemnity cap of 2x annual fees. Narrow fraud exception."),
                ("medium", "data_processing", "Data processing clause mentions DPDP but lacks explicit consent mechanism for employee data sharing.", "Add explicit DPDP Section 12 consent language for personal data."),
            ],
            "obligations": [
                ("Submit quarterly performance report (Q2 FY2026)", "reporting", "2025-09-30", "pending"),
                ("Renew Vendor Insurance Certificate — Public Liability", "compliance", "2025-07-15", "pending"),
            ],
            "comments": [
                ("Vikram Rao", "procurement", "Contract signed. Delivery schedules aligned with production plan. First PO issued."),
                ("Finance Team", "reviewer", "Payment terms of Net 45 approved with CFO exception. Monitor cash flow impact."),
                ("Legal Team", "reviewer", "High risk score due to liability and payment terms. Recommend renegotiation at renewal."),
            ],
        },
        {
            "id": "demo-c3",
            "title": "Employment Agreement — Rahul Verma (Senior Mechanical Engineer)",
            "contract_type": "employment",
            "status": "active",
            "counterparty_name": "Rahul Verma",
            "counterparty_email": "rahul.verma@acmemfg.in",
            "value_inr": 2_400_000,
            "risk_score": 0.35,
            "start_date": "2024-04-01",
            "end_date": "2027-03-31",
            "auto_renewal": False,
            "governing_law": "Laws of India",
            "parsed_text": EMPLOYMENT_TEXT,
            "clauses": [
                ("termination", "Employee may resign with 60 days notice. Employer may terminate with 3 months severance or 60 days notice. For cause: immediate.", 0.90),
                ("confidentiality", "Employee maintains confidentiality for 24 months post-employment. DPDP Act compliance required.", 0.85),
                ("payment", "Annual CTC INR 24,00,000 payable monthly. Bonus up to 20% of CTC. ESOPs: 2,000 options vesting over 4 years.", 0.92),
                ("governing_law", "Governed by laws of India. Labour Commissioner Pune for grievances. Courts at Pune have jurisdiction.", 0.94),
                ("intellectual_property", "All work product created during employment is company's exclusive property per Copyright Act 1957 Section 17.", 0.88),
                ("non_compete", "12-month non-compete and non-solicitation post-termination. India only. Reasonable scope per Section 27 ICA.", 0.72),
            ],
            "findings": [
                ("medium", "non_compete", "Non-compete of 12 months may be challenged under Section 27 Indian Contract Act as restraint of trade.", "Reduce to 6 months or replace with garden leave + enhanced confidentiality."),
                ("low", "termination", "Probation period of 6 months with 7-day notice is standard. Consider aligning with Labour Codes 2020.", "Monitor Labour Code implementation for probation rules."),
            ],
            "obligations": [
                ("Complete background verification — police and education check", "compliance", "2024-04-15", "completed"),
                ("Annual performance review — FY2025-26 appraisal cycle", "reporting", "2025-04-01", "pending"),
            ],
            "comments": [
                ("HR Team", "reviewer", "Background check cleared. PAN CDEFG5678H verified. Aadhaar 5678 9012 3456 verified."),
                ("Anand Mehta", "ceo", "Strong candidate. Approved CTC of INR 24L. ESOP grant approved by board."),
            ],
        },
        {
            "id": "demo-c4",
            "title": "Software License Agreement — CloudStack Technologies Pvt Ltd",
            "contract_type": "license",
            "status": "in_review",
            "counterparty_name": "CloudStack Technologies Pvt Ltd",
            "counterparty_email": "arjun.reddy@cloudstack.io",
            "value_inr": 3_500_000,
            "risk_score": 0.58,
            "start_date": "2024-06-10",
            "end_date": "2029-06-09",
            "auto_renewal": False,
            "governing_law": "Laws of India",
            "parsed_text": LICENSE_TEXT,
            "clauses": [
                ("termination", "Either Party may terminate for material breach with 30 days cure. Acme may terminate for convenience with 90 days notice.", 0.85),
                ("liability", "CloudStack liability capped at 12 months fees. No indirect damages. Exclusions: confidentiality breach, IP infringement, data breach.", 0.80),
                ("payment", "License fee INR 35,00,000 (50%/25%/25% milestones). Annual maintenance INR 7,00,000. Net 30. GST extra.", 0.88),
                ("data_processing", "India-only data storage (AWS Mumbai). AES-256 at rest, TLS 1.3 in transit. 72-hour breach notification. DPDP compliance.", 0.82),
                ("confidentiality", "CloudStack maintains confidentiality of Acme data. Five (5) years post-termination.", 0.86),
                ("governing_law", "Laws of India. Arbitration in Bangalore under Arbitration Act 1996. One arbitrator. English language.", 0.92),
                ("intellectual_property", "CloudStack retains Software IP. Acme owns its data. Customisations owned by Acme if fully paid.", 0.90),
                ("force_majeure", "Neither party liable for acts of God, war, epidemic, government action, internet outages beyond control.", 0.88),
            ],
            "findings": [
                ("high", "data_processing", "Data localisation to India required but clause does not explicitly prohibit sub-processors outside India.", "Add explicit prohibition on sub-processors outside India without RBI approval."),
                ("medium", "liability", "Liability cap of 12-month fees may be insufficient for data breach given DPDP penalties up to INR 250 crore.", "Increase liability cap for data breach to INR 5 crore or require cyber insurance."),
                ("medium", "termination", "Convenience termination by Acme with 90 days notice is generous. Pro-rata refund of AMC is fair.", "Consider reducing convenience notice to 60 days for better leverage."),
            ],
            "obligations": [
                ("UAT Sign-off — CloudStack ERP Manufacturing Module", "compliance", "2025-09-10", "pending"),
                ("DPDP Compliance Audit — CloudStack Data Processing", "compliance", "2025-12-31", "pending"),
            ],
            "comments": [
                ("Sneha Iyer", "cto", "Technical evaluation complete. CloudStack solution meets our requirements. Recommend proceeding with negotiation."),
                ("Legal Team", "reviewer", "Data localisation and liability clauses need strengthening before final approval."),
                ("Finance Team", "reviewer", "Budget approved. Milestone payment structure acceptable."),
            ],
        },
    ]

    for cd in contracts_data:
        # Generate PDF for demo contract
        pdf_path = f"./uploads/demo/{cd['id']}.pdf"
        generate_contract_pdf(
            contract_type=cd["contract_type"],
            title=cd["title"],
            party1="Acme Manufacturing Pvt Ltd",
            party2=cd["counterparty_name"],
            date=cd["start_date"],
            parsed_text=cd["parsed_text"],
            clauses=cd["clauses"],
            output_path=pdf_path,
        )

        contract = Contract(
            id=cd["id"], org_id="demo-org", title=cd["title"],
            contract_type=cd["contract_type"], status=cd["status"],
            counterparty_name=cd["counterparty_name"],
            counterparty_email=cd.get("counterparty_email", ""),
            value_inr=cd["value_inr"],
            risk_score=0.0,
            start_date=cd["start_date"],
            end_date=cd["end_date"],
            auto_renewal=cd["auto_renewal"],
            governing_law=cd["governing_law"],
            pdf_path=pdf_path,
            parsed_text=cd["parsed_text"],
        )
        session.add(contract)

        # Clauses
        for ctype, text, conf in cd["clauses"]:
            cl = ContractClause(
                contract_id=cd["id"], clause_type=ctype, clause_text=text,
                page_number=1, confidence_score=conf, extracted_by="seed"
            )
            session.add(cl)

        # Version
        version = ContractVersion(
            contract_id=cd["id"], version_number=1,
            title=cd["title"], pdf_path=pdf_path, parsed_text=cd["parsed_text"], created_by="seed"
        )
        session.add(version)

        # Approval stages
        stages = [
            ApprovalStage(contract_id=cd["id"], org_id="demo-org", stage_name="legal_review", status="completed", approver_name="Priya Nair", approver_email="priya@acmemfg.in", comment="Approved with noted risks."),
            ApprovalStage(contract_id=cd["id"], org_id="demo-org", stage_name="finance_review", status="completed" if cd["value_inr"] < 5_000_000 else "pending", approver_name="Vikram Rao", approver_email="vikram@acmemfg.in"),
            ApprovalStage(contract_id=cd["id"], org_id="demo-org", stage_name="ceo_review", status="pending" if cd["status"] == "in_review" else "completed", approver_name="Anand Mehta", approver_email="anand@acmemfg.in"),
        ]
        for s in stages:
            session.add(s)

        # Comments
        for author, role, content in cd.get("comments", []):
            cm = ContractComment(
                contract_id=cd["id"], org_id="demo-org",
                author_name=author, author_role=role, content=content,
            )
            session.add(cm)

        # Obligations linked to contract
        for desc, obtype, due, status in cd.get("obligations", []):
            ob = Obligation(
                contract_id=cd["id"], org_id="demo-org",
                description=desc, obligation_type=obtype,
                due_date=due, status=status,
            )
            session.add(ob)

    # ── Auto-generate highlights for demo contracts ──
    import pdfplumber
    color_map = {
        "termination": "rgba(239, 68, 68, 0.3)",
        "liability": "rgba(249, 115, 22, 0.3)",
        "indemnity": "rgba(245, 158, 11, 0.3)",
        "payment": "rgba(34, 197, 94, 0.3)",
        "confidentiality": "rgba(59, 130, 246, 0.3)",
        "governing_law": "rgba(139, 92, 246, 0.3)",
        "intellectual_property": "rgba(236, 72, 153, 0.3)",
        "force_majeure": "rgba(107, 114, 128, 0.3)",
        "data_processing": "rgba(14, 165, 233, 0.3)",
        "non_compete": "rgba(168, 85, 247, 0.3)",
        "default": "rgba(255, 179, 0, 0.3)",
    }

    for cd in contracts_data:
        pdf_path = f"./uploads/demo/{cd['id']}.pdf"
        if not os.path.exists(pdf_path):
            continue

        # Get clauses for this contract (need IDs from DB)
        res = await session.execute(select(ContractClause).where(ContractClause.contract_id == cd["id"]))
        db_clauses = res.scalars().all()

        with pdfplumber.open(pdf_path) as pdf:
            for cl in db_clauses:
                search_text = cl.clause_text[:80].strip()
                if len(search_text) < 10:
                    continue
                text_words = search_text.split()
                if len(text_words) < 3:
                    continue
                first_three = text_words[:3]
                found = False
                for page_idx, page in enumerate(pdf.pages):
                    if found:
                        break
                    words = page.extract_words()
                    for i, w in enumerate(words):
                        if i + 2 >= len(words):
                            continue
                        window = [words[i+j]["text"] for j in range(3)]
                        if window == first_three:
                            start = max(0, i - 2)
                            end = min(len(words), i + 20)
                            match_words = words[start:end]
                            xs = [w["x0"] for w in match_words]
                            ys = [w["top"] for w in match_words]
                            x1s = [w["x1"] for w in match_words]
                            y1s = [w["bottom"] for w in match_words]
                            x = min(xs)
                            y = min(ys)
                            w = max(x1s) - x
                            h = max(y1s) - y
                            pw, ph = page.width, page.height
                            if pw > 0 and ph > 0:
                                hl = ClauseHighlight(
                                    contract_id=cd["id"],
                                    clause_id=cl.id,
                                    clause_type=cl.clause_type,
                                    page_number=page_idx + 1,
                                    x=round(x / pw, 4),
                                    y=round(y / ph, 4),
                                    width=round(w / pw, 4),
                                    height=round(h / ph, 4),
                                    color=color_map.get(cl.clause_type, color_map["default"]),
                                )
                                session.add(hl)
                                found = True
                                break

    # ── Auto-generate plain english summaries for demo contracts ──
    for cd in contracts_data:
        # Build a map of findings by clause type for risk levels
        findings_map = {}
        for sev, ftype, desc, suggestion in cd.get("findings", []):
            findings_map[ftype] = {"severity": sev, "description": desc, "suggestion": suggestion}

        res = await session.execute(select(ContractClause).where(ContractClause.contract_id == cd["id"]))
        db_clauses = res.scalars().all()

        for cl in db_clauses:
            finding = findings_map.get(cl.clause_type)
            risk_level = finding["severity"] if finding else "low"
            risk_exp = finding["description"] if finding else "No significant risks identified in this clause."
            suggestion = finding["suggestion"] if finding else "No changes recommended."

            # Generate a simple plain-english summary
            plain = _generate_plain_english(cl.clause_type, cl.clause_text)

            pes = PlainEnglishSummary(
                contract_id=cd["id"],
                clause_id=cl.id,
                clause_type=cl.clause_type,
                original_text=cl.clause_text,
                plain_english=plain,
                risk_level=risk_level,
                risk_explanation=risk_exp,
                suggestions=suggestion,
            )
            session.add(pes)

    # ── Enrichment: Tree Index + Embeddings for demo contracts ──
    from app.services.pageindex_service import pageindex_service
    import math

    for cd in contracts_data:
        # Build tree from markdown
        tree_data = pageindex_service.build_tree_from_markdown(cd["parsed_text"], doc_name=cd["title"])
        flat_nodes = pageindex_service.flatten_tree(tree_data)
        tree_index = ContractTreeIndex(
            contract_id=cd["id"],
            org_id="demo-org",
            doc_name=cd["title"],
            structure=tree_data.get("structure", []),
            line_count=tree_data.get("line_count", 0),
            node_count=len(flat_nodes),
        )
        session.add(tree_index)

        # Seed embeddings (deterministic hash-based vectors, no API call)
        for i, cl in enumerate(cd["clauses"]):
            text = cl[1]
            # Create a simple 128-dim deterministic vector from text hash
            hash_val = hash(text) % (2 ** 31)
            vector = [math.sin(hash_val + i * j) * 0.5 for j in range(128)]
            ce = ContractEmbedding(
                contract_id=cd["id"],
                chunk_text=text[:500],
                embedding=vector,
                page_number=1,
                embedder="seed",
            )
            session.add(ce)

    await session.flush()
