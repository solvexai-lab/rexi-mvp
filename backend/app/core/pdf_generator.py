"""Generate realistic multi-page legal contract PDFs for demo data.

Uses fpdf2 with system fonts (Times New Roman) to create professional-looking
legal documents ~40 pages each, with proper formatting:
  - Title page with company letterhead
  - Table of contents
  - Numbered articles with bold headers
  - Indented paragraphs, defined terms
  - Page numbers in footer
  - Signature blocks and schedules
"""
import os
from fpdf import FPDF

# Use Windows system fonts (raw strings for Windows paths)
FONT_PATHS = {
    "TimesNR": r"C:\Windows\Fonts\times.ttf",
    "times_bold": r"C:\Windows\Fonts\timesbd.ttf",
    "times_italic": r"C:\Windows\Fonts\timesi.ttf",
    "times_bold_italic": r"C:\Windows\Fonts\timesbi.ttf",
    "ArialNR": r"C:\Windows\Fonts\arial.ttf",
    "arial_bold": r"C:\Windows\Fonts\arialbd.ttf",
}


def _nx():
    """Return new_x/new_y kwargs for cell() to avoid deprecation."""
    return {"new_x": "LMARGIN", "new_y": "NEXT"}


class LegalPDF(FPDF):
    def __init__(self):
        super().__init__(unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=25.4)
        self.set_margins(25.4, 25.4, 25.4)
        self._add_fonts()
        self.doc_title = ""

    def _add_fonts(self):
        # Use unique family names to avoid conflicts with fpdf2 core fonts
        FONT_NAMES = {
            "TimesNR": "TimesNR",
            "times_bold": "TimesNR",
            "times_italic": "TimesNR",
            "times_bold_italic": "TimesNR",
            "ArialNR": "ArialNR",
            "arial_bold": "ArialNR",
        }
        for name, path in FONT_PATHS.items():
            if os.path.exists(path):
                family = FONT_NAMES.get(name, name.split("_")[0])
                style = ""
                if "bold" in name and "italic" in name:
                    style = "BI"
                elif "bold" in name:
                    style = "B"
                elif "italic" in name:
                    style = "I"
                self.add_font(family, style, path)

    def header(self):
        if self.page_no() > 2:
            self.set_font("TimesNR", "", 9)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f"CONFIDENTIAL - {self.doc_title}", align="C", **_nx())
            self.ln(2)

    def footer(self):
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font("TimesNR", "", 9)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f"Page {self.page_no()}", align="C", **_nx())

    def title_page(self, title: str, party1: str, party2: str, date: str, contract_type: str):
        self.add_page()
        self.set_font("ArialNR", "B", 24)
        self.set_text_color(0, 0, 0)
        self.ln(40)
        self.cell(0, 15, title.upper(), align="C", **_nx())
        self.set_font("ArialNR", "", 12)
        self.ln(10)
        self.cell(0, 10, f"Contract Type: {contract_type.replace('_', ' ').title()}", align="C", **_nx())
        self.ln(30)
        self.set_font("TimesNR", "", 11)
        self.cell(0, 10, "Between", align="C", **_nx())
        self.ln(5)
        self.set_font("TimesNR", "B", 12)
        self.cell(0, 10, party1, align="C", **_nx())
        self.set_font("TimesNR", "", 11)
        self.cell(0, 10, '(hereinafter referred to as the "Company")', align="C", **_nx())
        self.ln(5)
        self.cell(0, 10, "And", align="C", **_nx())
        self.ln(5)
        self.set_font("TimesNR", "B", 12)
        self.cell(0, 10, party2, align="C", **_nx())
        self.set_font("TimesNR", "", 11)
        self.cell(0, 10, '(hereinafter referred to as the "Counterparty")', align="C", **_nx())
        self.ln(30)
        self.set_font("TimesNR", "", 11)
        self.cell(0, 10, f"Dated: {date}", align="C", **_nx())
        self.ln(20)
        self.set_font("TimesNR", "I", 9)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, "This document contains confidential and proprietary information.", align="C", **_nx())
        self.cell(0, 10, "Unauthorized disclosure, copying, or distribution is strictly prohibited.", align="C", **_nx())

    def toc_page(self):
        self.add_page()
        self.set_font("ArialNR", "B", 16)
        self.cell(0, 15, "TABLE OF CONTENTS", align="C", **_nx())
        self.ln(5)
        self.set_font("TimesNR", "", 11)
        sections = [
            ("Article 1", "Definitions and Interpretation"),
            ("Article 2", "Scope and Purpose"),
            ("Article 3", "Obligations of the Parties"),
            ("Article 4", "Term and Termination"),
            ("Article 5", "Compensation and Payment"),
            ("Article 6", "Confidentiality and Data Protection"),
            ("Article 7", "Intellectual Property Rights"),
            ("Article 8", "Representations and Warranties"),
            ("Article 9", "Indemnification and Limitation of Liability"),
            ("Article 10", "Force Majeure"),
            ("Article 11", "Dispute Resolution"),
            ("Article 12", "General Provisions"),
            ("Schedule A", "Defined Terms and Specifications"),
            ("Schedule B", "Insurance and Compliance Requirements"),
            ("Schedule C", "Data Processing and Security Standards"),
            ("Schedule D", "Service Level Agreements and KPIs"),
            ("Schedule E", "Change Management and Escalation Procedure"),
            ("Schedule F", "Exit Management and Transition"),
            ("Exhibit I", "Signature Page and Execution Formalities"),
        ]
        for num, title in sections:
            self.set_font("TimesNR", "B", 11)
            self.cell(50, 8, num, new_x="RIGHT", new_y="TOP")
            self.set_font("TimesNR", "", 11)
            self.cell(0, 8, title, **_nx())
            self.line(25.4, self.get_y(), 210 - 25.4, self.get_y())
            self.ln(2)

    def article_heading(self, number: str, title: str):
        self.ln(8)
        self.set_font("ArialNR", "B", 13)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, f"ARTICLE {number}", **_nx())
        self.set_font("ArialNR", "B", 12)
        self.cell(0, 8, title.upper(), **_nx())
        self.line(25.4, self.get_y(), 210 - 25.4, self.get_y())
        self.ln(4)

    def section_heading(self, number: str, title: str):
        self.ln(5)
        self.set_font("TimesNR", "B", 11)
        self.cell(0, 7, f"{number}.  {title}", **_nx())
        self.ln(1)

    def body_text(self, text: str, indent: bool = True):
        self.set_font("TimesNR", "", 11)
        self.set_text_color(0, 0, 0)
        if indent:
            self.set_x(35.4)
            self.multi_cell(210 - 35.4 - 25.4, 6, text)
        else:
            self.multi_cell(210 - 50.8, 6, text)
        self.ln(2)

    def numbered_para(self, number: int, text: str):
        self.set_font("TimesNR", "", 11)
        self.set_x(35.4)
        self.cell(10, 6, f"({number})", new_x="RIGHT", new_y="TOP")
        self.multi_cell(210 - 35.4 - 25.4 - 10, 6, text)
        self.ln(1)

    def bullet_para(self, text: str):
        self.set_font("TimesNR", "", 11)
        self.set_x(40.4)
        self.cell(8, 6, chr(149), new_x="RIGHT", new_y="TOP")
        self.multi_cell(210 - 40.4 - 25.4 - 8, 6, text)
        self.ln(1)

    def defined_term(self, term: str, definition: str):
        self.set_font("TimesNR", "B", 11)
        self.set_x(35.4)
        self.cell(0, 6, f'"{term}"', **_nx())
        self.set_font("TimesNR", "", 11)
        self.set_x(40.4)
        self.multi_cell(210 - 40.4 - 25.4, 6, f"means {definition}")
        self.ln(2)


# ──────────────────────────── Legal Boilerplate Content ────────────────────────────

def _definitions_articles():
    return [
        ("Affiliate", "any entity that directly or indirectly Controls, is Controlled by, or is under common Control with a Party. For the purposes of this definition, 'Control' means the ownership of more than fifty percent (50%) of the voting share capital of the relevant entity or the legal power to direct or cause the direction of the general management and policies of the relevant entity, whether through the ownership of voting securities, by contract, or otherwise."),
        ("Applicable Law", "all laws, statutes, regulations, ordinances, rules, codes, guidelines, orders, decrees, judgments, injunctions, writs, or other legal requirements of any governmental authority having jurisdiction over the Parties, including but not limited to the Indian Contract Act, 1872, the Information Technology Act, 2000, the Digital Personal Data Protection Act, 2023, the Arbitration and Conciliation Act, 1996, and all rules, regulations, notifications, and circulars issued thereunder, as amended from time to time."),
        ("Business Day", "any day other than a Saturday, Sunday, or any day on which banks are authorised or required to be closed in Mumbai, India."),
        ("Confidential Information", "all non-public, proprietary, or confidential information disclosed by either Party (the 'Disclosing Party') to the other Party (the 'Receiving Party'), whether orally, in writing, electronically, or by any other means, including but not limited to technical data, know-how, research, product plans, software code, algorithms, customer lists, pricing information, financial data, marketing strategies, business processes, and any other information designated as confidential at the time of disclosure or that reasonably should be understood to be confidential given the nature of the information and the circumstances of disclosure."),
        ("Data Breach", "any unauthorised access, acquisition, use, disclosure, modification, or destruction of Personal Data, or any other breach of security safeguards that compromises the confidentiality, integrity, or availability of Personal Data, whether accidental or deliberate, including any incident that results in the unauthorised disclosure of Personal Data to any third party."),
        ("Effective Date", "the date first written above, or such other date as the Parties may agree in writing."),
        ("Force Majeure Event", "any event beyond the reasonable control of a Party, including but not limited to acts of God, war, terrorism, riots, embargoes, acts of civil or military authorities, fire, floods, accidents, strikes, epidemics, pandemics, quarantine restrictions, shortages of labour or materials, failure of utilities or transportation, failure of internet service providers, hacking, denial of service attacks, or other cyber incidents, governmental actions, or any other cause beyond the reasonable control of the affected Party."),
        ("Intellectual Property Rights", "all patents, patent applications, copyrights, trademarks, service marks, trade names, domain names, rights in designs, rights in computer software, database rights, rights in confidential information (including know-how and trade secrets), and any other intellectual property rights, in each case whether registered or unregistered, and including all applications for, and renewals or extensions of, such rights, and all similar or equivalent rights or forms of protection which subsist or will subsist now or in the future in any part of the world."),
        ("Personal Data", "any information relating to an identified or identifiable natural person ('Data Principal'), including but not limited to name, address, email address, phone number, government identification numbers (such as PAN, Aadhaar, passport number), financial information, biometric data, genetic data, and any other data as defined under the Digital Personal Data Protection Act, 2023."),
        ("Services", "the services to be performed by the Counterparty as described in this Agreement, the Statement of Work, and any other documents incorporated by reference herein."),
        ("Term", "the period commencing on the Effective Date and continuing until the expiration or termination of this Agreement in accordance with its terms."),
        ("Third Party", "any person or entity other than the Parties and their respective Affiliates."),
        ("Working Day", "a day (other than a Saturday or Sunday) on which banks are open for general business in Mumbai, India."),
        ("Change of Control", "any transaction or series of transactions resulting in the acquisition by any person or group of persons of more than fifty percent (50%) of the voting share capital or assets of a Party, or any merger, consolidation, amalgamation, or reorganisation of a Party with or into any other entity, or any sale, lease, transfer, or other disposition of all or substantially all of the assets of a Party."),
        ("Deliverables", "all documents, software, code, designs, drawings, specifications, reports, data, materials, and other items to be delivered by the Counterparty to the Company in connection with the Services, as specified in the Statement of Work or as otherwise agreed by the Parties."),
        ("Statement of Work", "a document executed by the Parties describing the specific Services, Deliverables, timelines, milestones, acceptance criteria, and fees for a particular engagement, which document is incorporated into and made a part of this Agreement by reference."),
        ("Acceptance Criteria", "the specific functional, technical, performance, and quality standards that the Deliverables must meet in order to be accepted by the Company, as set forth in the applicable Statement of Work or as otherwise agreed in writing by the Parties."),
        ("Background IP", "all Intellectual Property Rights owned or controlled by a Party prior to the Effective Date or developed independently of this Agreement during the Term."),
        ("Foreground IP", "all Intellectual Property Rights conceived, developed, or created by either Party in the performance of the Services or in connection with this Agreement during the Term."),
    ]


def _general_provisions():
    return [
        ("12.1", "Entire Agreement", "This Agreement, together with all Schedules and Exhibits hereto, constitutes the entire agreement between the Parties with respect to the subject matter hereof and supersedes all prior and contemporaneous agreements, proposals, understandings, negotiations, and discussions, whether oral or written, between the Parties relating to such subject matter. No amendment, modification, or waiver of any provision of this Agreement shall be effective unless in writing and signed by authorised representatives of both Parties."),
        ("12.2", "Severability", "If any provision of this Agreement is held by a court of competent jurisdiction to be invalid, illegal, or unenforceable, such provision shall be modified to the minimum extent necessary to make it valid, legal, and enforceable, or if such modification is not possible, such provision shall be severed from this Agreement, and the remaining provisions shall continue in full force and effect. The Parties agree to negotiate in good faith to replace any invalid, illegal, or unenforceable provision with a valid, legal, and enforceable provision that achieves the closest economic and commercial effect to the original provision."),
        ("12.3", "Waiver", "No waiver of any provision of this Agreement shall be effective unless in writing and signed by the Party against whom the waiver is sought to be enforced. No failure or delay by either Party in exercising any right, power, or remedy under this Agreement shall operate as a waiver thereof, nor shall any single or partial exercise of any such right, power, or remedy preclude any other or further exercise thereof or the exercise of any other right, power, or remedy."),
        ("12.4", "Assignment", "Neither Party may assign, transfer, or novate this Agreement or any of its rights or obligations hereunder without the prior written consent of the other Party, except that either Party may assign this Agreement to an Affiliate or to a successor in connection with a merger, acquisition, corporate reorganisation, or sale of all or substantially all of its assets, provided that the assignee agrees in writing to be bound by the terms of this Agreement. Any purported assignment in violation of this Section shall be null and void."),
        ("12.5", "Notices", "All notices, requests, demands, claims, and other communications hereunder shall be in writing and shall be deemed to have been duly given (a) when delivered by hand (with written confirmation of receipt), (b) when received by the addressee if sent by a nationally recognised overnight courier (receipt requested), (c) on the date sent by email (with confirmation of transmission) if sent during normal business hours of the recipient, and on the next business day if sent after normal business hours, or (d) on the third business day after the date mailed, by certified or registered mail, return receipt requested, postage prepaid. All notices shall be sent to the addresses set forth above or to such other address as a Party may designate by notice given in accordance with this Section."),
        ("12.6", "Governing Law and Jurisdiction", "This Agreement shall be governed by and construed in accordance with the laws of India, without regard to its conflict of laws principles. Any dispute, controversy, or claim arising out of or relating to this Agreement, including the formation, interpretation, breach, termination, or validity thereof, shall be resolved exclusively through arbitration in accordance with the Arbitration and Conciliation Act, 1996, as amended from time to time. The arbitration shall be conducted in English, in Mumbai, India, by a sole arbitrator appointed by mutual agreement of the Parties. If the Parties fail to agree on the appointment of the arbitrator within thirty (30) days from the date of referral to arbitration, the arbitrator shall be appointed by the Chief Justice of the Bombay High Court or any person or institution designated by him. The award of the arbitrator shall be final and binding on the Parties, and judgment upon the award may be entered in any court having jurisdiction thereof. The Parties hereby irrevocably submit to the exclusive jurisdiction of the courts at Mumbai, India, for the purposes of enforcing any arbitral award."),
        ("12.7", "Counterparts", "This Agreement may be executed in one or more counterparts, each of which shall be deemed an original and all of which together shall constitute one and the same instrument. Electronic signatures and scanned copies transmitted by email or other electronic means shall have the same legal effect as original signatures and originals for all purposes."),
        ("12.8", "Third Party Beneficiaries", "Except as expressly provided herein, nothing in this Agreement, express or implied, is intended to or shall confer upon any Third Party any legal or equitable right, benefit, or remedy of any nature whatsoever under or by reason of this Agreement."),
        ("12.9", "Relationship of Parties", "Nothing in this Agreement shall be construed as creating an agency, partnership, joint venture, fiduciary, or employment relationship between the Parties. The Counterparty is an independent contractor and neither Party has the authority to bind the other Party or to incur any obligation on behalf of the other Party except as expressly authorised in writing by such other Party."),
        ("12.10", "Survival", "All provisions of this Agreement that by their nature should survive termination or expiration of this Agreement, including but not limited to Articles 6 (Confidentiality), 7 (Intellectual Property), 9 (Indemnification), 11 (Dispute Resolution), and this Article 12 (General Provisions), shall survive such termination or expiration for the periods specified therein or, if no period is specified, indefinitely."),
        ("12.11", "Export Control", "The Parties shall comply with all applicable export control laws and regulations of India and any other relevant jurisdiction, including but not limited to the Weapons of Mass Destruction and their Delivery Systems (Prohibition of Unlawful Activities) Act, 2005, and shall not export, re-export, or transfer any goods, software, technology, or technical data in violation of such laws and regulations."),
        ("12.12", "Anti-Bribery and Anti-Corruption", "Each Party represents and warrants that it has not and shall not, in connection with the performance of its obligations under this Agreement, directly or indirectly, offer, pay, promise to pay, or authorise the payment of any money, gift, or anything of value to any government official, political party, or candidate for public office for the purpose of influencing any act or decision of such person or entity in order to obtain or retain business or secure any improper advantage. Each Party shall comply with all applicable anti-bribery and anti-corruption laws, including but not limited to the Prevention of Corruption Act, 1988."),
        ("12.13", "Publicity", "Neither Party shall issue any press release, advertisement, or other public announcement relating to this Agreement or the transactions contemplated hereby without the prior written consent of the other Party, except as required by Applicable Law or the rules of any stock exchange on which the Party's securities are listed. Notwithstanding the foregoing, the Counterparty may include the Company's name and logo in its customer list and marketing materials, subject to the Company's brand guidelines and prior written approval of any specific use."),
        ("12.14", "Further Assurances", "Each Party shall, at its own cost and expense, execute and deliver all further documents and instruments, and take all further actions, that may be necessary or desirable to give effect to the provisions of this Agreement and to consummate the transactions contemplated hereby."),
        ("12.15", "Language", "This Agreement is executed in the English language. In the event of any conflict or ambiguity between the English version and any translation thereof, the English version shall prevail. All notices, reports, and other communications under this Agreement shall be in English."),
        ("12.16", "Compliance with Laws", "Each Party shall comply with all Applicable Laws in the performance of its obligations under this Agreement, including but not limited to tax laws, labour laws, environmental laws, data protection laws, and export control laws. The Counterparty shall maintain all necessary licences, permits, and registrations required for the performance of the Services and shall promptly notify the Company of any material change in its compliance status."),
    ]


def _representations_warranties():
    return [
        ("8.1", "Mutual Representations", "Each Party represents and warrants to the other Party that: (a) it is duly organised, validly existing, and in good standing under the laws of the jurisdiction of its incorporation or formation; (b) it has the full power and authority to enter into this Agreement and to perform its obligations hereunder; (c) the execution, delivery, and performance of this Agreement have been duly authorised by all necessary corporate or other organisational action; (d) this Agreement constitutes a legal, valid, and binding obligation of such Party, enforceable against it in accordance with its terms, subject to applicable bankruptcy, insolvency, reorganisation, moratorium, or similar laws affecting creditors' rights generally and general principles of equity; and (e) the execution, delivery, and performance of this Agreement does not and will not conflict with, violate, or result in a breach of any agreement, instrument, judgment, order, decree, or law to which it is a party or by which it is bound."),
        ("8.2", "Company Representations", "The Company represents and warrants that: (a) it owns or has valid licences to all Intellectual Property Rights necessary for the performance of its obligations under this Agreement; (b) it has complied and shall continue to comply with all Applicable Laws, including but not limited to labour laws, tax laws, environmental laws, and data protection laws; (c) it maintains adequate insurance coverage, including but not limited to general liability insurance, professional indemnity insurance, and cyber liability insurance, with reputable insurers and in amounts customary for companies of similar size and nature; (d) all financial statements and representations made by the Company to the Counterparty are true, accurate, and complete in all material respects; and (e) it has disclosed to the Counterparty all material facts and circumstances that could reasonably be expected to affect the Counterparty's decision to enter into this Agreement."),
        ("8.3", "Counterparty Representations", "The Counterparty represents and warrants that: (a) it possesses the necessary qualifications, expertise, experience, and resources to perform the Services in a professional and workmanlike manner, in accordance with industry standards and best practices; (b) all personnel assigned to perform the Services shall be suitably qualified, trained, and experienced, and shall comply with all Applicable Laws and the Company's policies and procedures; (c) the Services and all deliverables provided under this Agreement shall be original works, shall not infringe upon the Intellectual Property Rights of any Third Party, and shall be free from any viruses, malware, spyware, or other harmful code; (d) it has obtained and shall maintain all necessary licences, permits, registrations, and approvals required for the performance of the Services; and (e) it shall comply with all Applicable Laws, including but not limited to tax laws, labour laws, and data protection laws, in the performance of its obligations under this Agreement."),
        ("8.4", "Disclaimer", "EXCEPT AS EXPRESSLY SET FORTH IN THIS AGREEMENT, NEITHER PARTY MAKES ANY REPRESENTATIONS OR WARRANTIES OF ANY KIND, WHETHER EXPRESS, IMPLIED, STATUTORY, OR OTHERWISE, INCLUDING BUT NOT LIMITED TO ANY IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE, NON-INFRINGEMENT, OR ACCURACY. THE COMPANY DOES NOT WARRANT THAT THE SERVICES WILL BE UNINTERRUPTED, TIMELY, SECURE, OR ERROR-FREE."),
    ]


def _force_majeure():
    return [
        ("10.1", "Excused Performance", "Neither Party shall be liable to the other Party for any failure or delay in the performance of its obligations under this Agreement (other than obligations to make payments) to the extent such failure or delay is caused by a Force Majeure Event. Upon the occurrence of a Force Majeure Event, the affected Party shall promptly notify the other Party in writing, describing the nature of the Force Majeure Event, the anticipated duration of the delay, and the obligations affected thereby."),
        ("10.2", "Mitigation", "The affected Party shall use commercially reasonable efforts to mitigate the effects of the Force Majeure Event, to resume performance of its obligations as soon as practicable, and to minimise the duration and impact of the delay. The affected Party shall provide the other Party with regular updates regarding the status of the Force Majeure Event and the efforts being made to resume performance."),
        ("10.3", "Termination for Extended Force Majeure", "If a Force Majeure Event continues for a period of more than sixty (60) consecutive days, either Party may terminate this Agreement upon written notice to the other Party, without liability to the other Party, except for obligations that accrued prior to the Force Majeure Event and obligations that survive termination pursuant to Section 12.10. Upon such termination, the Company shall pay the Counterparty for all Services performed and expenses incurred up to the date of termination."),
    ]


def _dispute_resolution():
    return [
        ("11.1", "Good Faith Negotiation", "In the event of any dispute, controversy, or claim arising out of or relating to this Agreement, the Parties shall first attempt in good faith to resolve the dispute through informal negotiation between senior executives of the Parties who have authority to settle the dispute. Either Party may initiate such negotiation by providing written notice to the other Party describing the dispute and requesting a meeting. The Parties shall meet within fifteen (15) Business Days of such notice and shall negotiate in good faith for a period of not less than thirty (30) days."),
        ("11.2", "Mediation", "If the Parties are unable to resolve the dispute through good faith negotiation within thirty (30) days, either Party may, by written notice to the other Party, refer the dispute to mediation in accordance with the Mediation and Conciliation Rules of the Indian Institute of Arbitration and Mediation. The mediation shall be conducted in English, in Mumbai, India, by a mediator appointed by mutual agreement of the Parties. If the Parties fail to agree on the appointment of the mediator within fifteen (15) days from the date of referral to mediation, the mediator shall be appointed by the Indian Institute of Arbitration and Mediation. The costs of mediation shall be borne equally by the Parties."),
        ("11.3", "Arbitration", "If the dispute is not resolved through mediation within sixty (60) days from the date of referral to mediation, either Party may refer the dispute to binding arbitration in accordance with Section 12.6 (Governing Law and Jurisdiction). The arbitration proceedings shall be confidential, and neither Party shall disclose the existence, content, or results of any arbitration proceeding to any Third Party without the prior written consent of the other Party, except as required by Applicable Law or to enforce the arbitral award."),
        ("11.4", "Injunctive Relief", "Notwithstanding the foregoing, either Party may seek interim or conservatory measures, including injunctive relief, attachment, or other equitable remedies, from a court of competent jurisdiction to prevent irreparable harm, preserve the status quo, or enforce confidentiality obligations, without prejudice to the Parties' agreement to resolve the underlying dispute through arbitration."),
        ("11.5", "Costs and Attorneys' Fees", "In any arbitration or litigation arising out of or relating to this Agreement, the prevailing Party shall be entitled to recover from the non-prevailing Party all reasonable costs, expenses, and attorneys' fees incurred in connection with such proceedings, in addition to any other relief granted."),
    ]


def _schedules():
    return [
        ("SCHEDULE A", "DEFINED TERMS AND SPECIFICATIONS", [
            "A.1  The following specifications and technical requirements apply to all Services performed under this Agreement:",
            "A.2  All deliverables shall conform to the quality standards set forth in ISO 9001:2015 and shall be subject to quality assurance review by the Company.",
            "A.3  The Counterparty shall maintain comprehensive documentation of all Services performed, including but not limited to design documents, source code, test plans, test results, user manuals, and maintenance guides.",
            "A.4  All software deliverables shall be developed using industry-standard coding conventions, shall be properly commented, and shall include unit tests achieving a minimum code coverage of eighty percent (80%).",
            "A.5  The Counterparty shall provide the Company with access to all project management tools, version control systems, and collaboration platforms used in the performance of the Services.",
            "A.6  All hardware and equipment used in the performance of the Services shall comply with relevant BIS (Bureau of Indian Standards) certifications and shall be maintained in good working condition.",
            "A.7  The Counterparty shall ensure that all personnel assigned to the project have signed appropriate confidentiality and non-disclosure agreements.",
            "A.8  The Counterparty shall conduct background verification checks on all personnel who will have access to the Company's Confidential Information or systems.",
        ]),
        ("SCHEDULE B", "INSURANCE AND COMPLIANCE REQUIREMENTS", [
            "B.1  The Counterparty shall maintain, at its own expense, the following insurance coverage throughout the Term:",
            "     (a) Comprehensive General Liability Insurance with minimum coverage of INR 5,00,00,000 (Rupees Five Crores) per occurrence and INR 10,00,00,000 (Rupees Ten Crores) in aggregate;",
            "     (b) Professional Indemnity / Errors and Omissions Insurance with minimum coverage of INR 5,00,00,000 (Rupees Five Crores) per claim and in aggregate;",
            "     (c) Cyber Liability Insurance with minimum coverage of INR 10,00,00,000 (Rupees Ten Crores) per claim and in aggregate;",
            "     (d) Workers' Compensation Insurance as required by Applicable Law; and",
            "     (e) Directors and Officers Liability Insurance with minimum coverage of INR 2,50,00,000 (Rupees Two Crores and Fifty Lakhs).",
            "B.2  The Counterparty shall provide the Company with certificates of insurance evidencing the coverage required herein within fifteen (15) days of the Effective Date and annually thereafter.",
            "B.3  The Counterparty shall comply with all applicable statutory and regulatory requirements, including but not limited to GST registration and compliance, PF and ESI contributions, professional tax, and all other applicable labour and employment laws.",
            "B.4  The Counterparty represents that it is not debarred, suspended, or otherwise ineligible to participate in government contracts, and that it has not been convicted of any criminal offence involving fraud, dishonesty, or breach of trust.",
            "B.5  The Counterparty shall promptly notify the Company of any material change in its insurance coverage, financial condition, or legal status that could affect its ability to perform its obligations under this Agreement.",
        ]),
        ("SCHEDULE C", "DATA PROCESSING AND SECURITY STANDARDS", [
            "C.1  The Counterparty shall implement and maintain appropriate technical and organisational measures to protect Personal Data against unauthorised or unlawful processing, accidental loss, destruction, damage, alteration, or disclosure.",
            "C.2  Such measures shall include, at a minimum:",
            "     (a) Encryption of Personal Data at rest using AES-256 or equivalent encryption standards;",
            "     (b) Encryption of Personal Data in transit using TLS 1.3 or equivalent protocols;",
            "     (c) Multi-factor authentication for all access to systems containing Personal Data;",
            "     (d) Regular security audits and vulnerability assessments, conducted at least quarterly;",
            "     (e) Implementation of intrusion detection and prevention systems;",
            "     (f) Regular backup and disaster recovery procedures, with backups stored in geographically separate locations; and",
            "     (g) Comprehensive access controls and logging mechanisms.",
            "C.3  The Counterparty shall notify the Company of any Data Breach within twenty-four (24) hours of discovery and shall cooperate fully with the Company in investigating and remediating such breach.",
            "C.4  The Counterparty shall ensure that all sub-processors engaged in the processing of Personal Data are bound by written agreements imposing data protection obligations substantially similar to those set forth in this Agreement.",
            "C.5  Upon termination or expiration of this Agreement, the Counterparty shall, at the Company's election, return or securely destroy all Personal Data and provide written certification of such destruction.",
            "C.6  The Counterparty shall maintain records of all processing activities carried out on behalf of the Company and shall make such records available to the Company upon request.",
        ]),
        ("SCHEDULE D", "SERVICE LEVEL AGREEMENTS AND KEY PERFORMANCE INDICATORS", [
            "D.1  The following Service Level Agreements ('SLAs') shall apply to the Services:",
            "     (a) Availability: The Services shall be available 99.9% of the time, measured monthly, excluding scheduled maintenance windows and Force Majeure Events;",
            "     (b) Response Time: The Counterparty shall acknowledge all support requests within four (4) hours of receipt during Business Days;",
            "     (c) Resolution Time: Critical issues shall be resolved within twenty-four (24) hours, high-priority issues within seventy-two (72) hours, and medium-priority issues within five (5) Business Days;",
            "     (d) Deliverable Quality: All Deliverables shall meet the Acceptance Criteria and shall have zero critical defects and no more than five (5) high-priority defects;",
            "     (e) Reporting Accuracy: All reports and data provided by the Counterparty shall be accurate to within 99.5%; and",
            "     (f) Security Compliance: The Counterparty shall maintain 100% compliance with the security standards specified in Schedule C.",
            "D.2  Service Credits: If the Counterparty fails to meet any SLA in a given month, the Company shall be entitled to service credits as follows: (a) 5% of monthly fees for each 0.1% below the availability target; (b) 2% of monthly fees for each missed response time target; (c) 3% of monthly fees for each missed resolution time target; and (d) 10% of monthly fees for any security compliance failure.",
            "D.3  Reporting: The Counterparty shall provide monthly SLA performance reports to the Company within five (5) Business Days of the end of each month. Such reports shall include detailed metrics, root cause analyses for any failures, and corrective action plans.",
            "D.4  Review: The Parties shall meet quarterly to review SLA performance, discuss any issues or concerns, and agree on any necessary adjustments to the SLAs or the Services.",
            "D.5  Continuous Improvement: The Counterparty shall implement a continuous improvement programme to enhance the quality, efficiency, and reliability of the Services. The Counterparty shall provide the Company with an annual improvement plan and shall report on progress against such plan on a quarterly basis.",
        ]),
        ("SCHEDULE E", "CHANGE MANAGEMENT AND ESCALATION PROCEDURE", [
            "E.1  Any change to the scope, timelines, fees, or other terms of this Agreement or any Statement of Work shall be governed by the following change management procedure:",
            "     (a) Change Request: Either Party may submit a written change request describing the proposed change, the rationale therefor, and the anticipated impact on scope, timelines, fees, and resources;",
            "     (b) Impact Assessment: The Counterparty shall provide a detailed impact assessment within five (5) Business Days of receipt of the change request, including revised timelines, resource requirements, and fee estimates;",
            "     (c) Approval: The change shall not be implemented until both Parties have approved the impact assessment in writing; and",
            "     (d) Implementation: Upon approval, the Counterparty shall implement the change in accordance with the approved impact assessment and shall provide regular status updates to the Company.",
            "E.2  Emergency Changes: In the event of an emergency requiring immediate action to prevent harm, damage, or material disruption, either Party may implement an emergency change without prior written approval, provided that the implementing Party promptly notifies the other Party and provides a retrospective impact assessment within twenty-four (24) hours.",
            "E.3  Escalation Procedure: If any dispute, issue, or concern arises in connection with the performance of the Services that cannot be resolved at the operational level within five (5) Business Days, either Party may escalate the matter to the designated escalation contacts. The escalation contacts shall meet within three (3) Business Days and shall use best efforts to resolve the matter within ten (10) Business Days.",
            "E.4  Governance Committee: The Parties shall establish a governance committee comprising senior representatives from each Party. The governance committee shall meet monthly (or as otherwise agreed) to review performance, address issues, approve changes, and ensure alignment between the Parties.",
            "E.5  Documentation: All changes, escalations, and governance committee decisions shall be documented in writing and shall be incorporated into this Agreement or the applicable Statement of Work by reference.",
            "E.6  Change Control Board: For changes exceeding INR 10,00,000 in value or requiring more than twenty (20) additional person-days of effort, the Parties shall convene a Change Control Board comprising senior executives from each Party. The Change Control Board shall review the change request, assess risks and benefits, and make a binding decision within ten (10) Business Days.",
            "E.7  Version Control: All versions of this Agreement, Statements of Work, and change documentation shall be maintained in a centralised document repository accessible to both Parties. Each version shall be numbered, dated, and accompanied by a change log describing all modifications.",
        ]),
        ("SCHEDULE F", "EXIT MANAGEMENT AND TRANSITION", [
            "F.1  Upon expiration or termination of this Agreement for any reason, the Parties shall cooperate in good faith to ensure an orderly transition of the Services to the Company or a replacement vendor designated by the Company.",
            "F.2  Transition Plan: No later than ninety (90) days prior to the anticipated expiration or termination date, the Counterparty shall submit a detailed transition plan to the Company for approval. The transition plan shall include: (a) a timeline for transition activities; (b) a list of all Deliverables, data, documentation, and materials to be transferred; (c) a knowledge transfer plan, including training sessions and documentation; (d) a plan for the orderly termination of subcontractor relationships; and (e) a communication plan for notifying affected employees, customers, and other stakeholders.",
            "F.3  Knowledge Transfer: The Counterparty shall provide comprehensive knowledge transfer to the Company's personnel or the replacement vendor's personnel, including but not limited to: (a) detailed documentation of all systems, processes, and procedures; (b) training sessions on the operation and maintenance of all systems and deliverables; (c) access to all source code, configuration files, and technical documentation; and (d) introduction to all key contacts, vendors, and subcontractors.",
            "F.4  Data Transfer: The Counterparty shall transfer all Company data, Confidential Information, and other materials to the Company or its designated recipient in a format agreed by the Parties. The Counterparty shall ensure the integrity, accuracy, and completeness of all transferred data and shall provide written certification thereof.",
            "F.5  Parallel Operation: To the extent practicable, the Counterparty shall provide parallel operation support during the transition period, ensuring continuity of service while the Company or replacement vendor assumes responsibility for the Services.",
            "F.6  Exit Assistance: For a period of up to six (6) months following termination or expiration, the Counterparty shall provide reasonable exit assistance at mutually agreed rates, including but not limited to: (a) answering questions and providing clarifications; (b) troubleshooting issues; (c) providing additional training; and (d) assisting with the integration of replacement systems or vendors.",
            "F.7  Termination Fees: If the Company terminates this Agreement for convenience, the Company shall pay the Counterparty a termination fee equal to twenty percent (20%) of the fees that would have been payable for the remaining Term, provided that such termination fee shall not exceed INR 50,00,000. No termination fee shall be payable if the Company terminates for cause or if the Counterparty terminates for convenience.",
        ]),
    ]


def _signature_page(party1: str, party2: str):
    return [
        ("EXHIBIT I", "SIGNATURE PAGE AND EXECUTION FORMALITIES", [
            "IN WITNESS WHEREOF, the Parties have executed this Agreement as of the date first written above.",
            "",
            f"FOR AND ON BEHALF OF {party1.upper()}",
            "",
            "Signature: _____________________________",
            "Name: ________________________________",
            "Title: ________________________________",
            "Date: ________________________________",
            "",
            "Witness:",
            "Signature: _____________________________",
            "Name: ________________________________",
            "Address: _____________________________",
            "",
            f"FOR AND ON BEHALF OF {party2.upper()}",
            "",
            "Signature: _____________________________",
            "Name: ________________________________",
            "Title: ________________________________",
            "Date: ________________________________",
            "",
            "Witness:",
            "Signature: _____________________________",
            "Name: ________________________________",
            "Address: _____________________________",
        ]),
    ]


# ──────────────────────────── Main Generator ────────────────────────────

def generate_contract_pdf(contract_type: str, title: str, party1: str, party2: str,
                          date: str, parsed_text: str, clauses: list,
                          output_path: str) -> str:
    """Generate a realistic ~40-page legal contract PDF. Returns the output file path."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    pdf = LegalPDF()
    pdf.doc_title = title

    # 1. Title page
    pdf.title_page(title, party1, party2, date, contract_type)

    # 2. Table of Contents
    pdf.toc_page()

    # 3. Recitals / Preamble
    pdf.add_page()
    pdf.set_font("ArialNR", "B", 14)
    pdf.cell(0, 12, "RECITALS", align="C", **_nx())
    pdf.ln(5)
    pdf.set_font("TimesNR", "", 11)
    recitals = [
        f"WHEREAS, {party1} (the 'Company') is a company incorporated under the laws of India, engaged in the business of manufacturing and technology services;",
        f"WHEREAS, {party2} (the 'Counterparty') is a company/person engaged in providing goods and/or services relevant to the Company's business operations;",
        "WHEREAS, the Company desires to engage the Counterparty for the provision of certain goods and/or services, and the Counterparty desires to provide such goods and/or services to the Company, all on the terms and conditions set forth herein;",
        "WHEREAS, the Parties wish to set forth their respective rights, obligations, and responsibilities in connection with the engagement;",
        "NOW, THEREFORE, in consideration of the mutual covenants, promises, and agreements set forth herein, and for other good and valuable consideration, the receipt and sufficiency of which are hereby acknowledged, the Parties agree as follows:",
    ]
    for r in recitals:
        pdf.multi_cell(210 - 50.8, 6, r)
        pdf.ln(3)

    # 4. Article 1: Definitions
    pdf.article_heading("1", "Definitions and Interpretation")
    pdf.body_text("Unless the context otherwise requires, the following terms shall have the meanings set forth below:")
    for term, definition in _definitions_articles():
        pdf.defined_term(term, definition)
    pdf.body_text("In this Agreement, unless the context otherwise requires: (a) words denoting the singular shall include the plural and vice versa; (b) words denoting any gender shall include all genders; (c) references to 'writing' or 'written' include any mode of reproducing words in a legible and non-transitory form; (d) references to 'days' are to calendar days unless expressly stated to be Business Days; (e) the words 'include', 'including', and 'in particular' shall be construed as being by way of illustration or emphasis only and shall not be construed as limiting the generality of any preceding words; and (f) any reference to a statute, statutory provision, or subordinate legislation is a reference to it as it is in force from time to time, taking account of any amendment, extension, or re-enactment.")

    # 5. Article 2: Scope and Purpose (contract-specific)
    pdf.article_heading("2", "Scope and Purpose")
    pdf.section_heading("2.1", "General Scope")
    pdf.body_text("This Article sets forth the scope, objectives, and deliverables of the engagement between the Parties. The Counterparty shall perform the Services and deliver the Deliverables in accordance with the terms and conditions of this Agreement, the applicable Statement of Work, and any other documents incorporated by reference herein. The Services shall be performed in a professional and workmanlike manner, in accordance with industry standards and best practices, and shall meet the Acceptance Criteria specified in the applicable Statement of Work or as otherwise agreed in writing by the Parties.")
    pdf.section_heading("2.2", "Detailed Description")
    pdf.body_text(parsed_text, indent=True)
    pdf.section_heading("2.3", "Exclusions")
    pdf.body_text("Unless expressly set forth in a Statement of Work or otherwise agreed in writing by the Parties, the Counterparty shall have no obligation to perform any services, provide any deliverables, or assume any responsibilities that are not expressly described in this Agreement or the applicable Statement of Work. Without limiting the generality of the foregoing, the Counterparty shall not be responsible for: (a) any services or deliverables that are outside the scope of the Statement of Work; (b) any delays or failures caused by the Company's failure to provide necessary information, access, resources, or cooperation; (c) any changes to the Services or Deliverables requested by the Company that are not made in accordance with the change management procedure set forth in Schedule E; or (d) any consequences arising from the Company's misuse, modification, or unauthorised distribution of the Deliverables.")
    pdf.section_heading("2.4", "Statement of Work")
    pdf.body_text("The specific Services, Deliverables, timelines, milestones, Acceptance Criteria, and fees for each engagement shall be set forth in a Statement of Work executed by the Parties. Each Statement of Work shall be incorporated into and made a part of this Agreement by reference. In the event of any conflict or inconsistency between the terms of this Agreement and a Statement of Work, the terms of this Agreement shall prevail unless the Statement of Work expressly states that it supersedes a specific provision of this Agreement. No Statement of Work shall be binding unless executed by authorised representatives of both Parties.")
    pdf.section_heading("2.5", "Acceptance")
    pdf.body_text("The Company shall review and test each Deliverable in accordance with the Acceptance Criteria set forth in the applicable Statement of Work. Within fifteen (15) Business Days of delivery of a Deliverable, the Company shall either: (a) accept the Deliverable in writing; (b) reject the Deliverable in writing, specifying in reasonable detail the defects, errors, or non-conformities that prevent acceptance; or (c) request a reasonable extension of the review period, not to exceed ten (10) Business Days. If the Company fails to respond within the applicable period, the Deliverable shall be deemed accepted. The Counterparty shall correct all identified defects, errors, or non-conformities within ten (10) Business Days of receipt of the rejection notice and shall resubmit the corrected Deliverable for acceptance. Acceptance of a Deliverable shall not relieve the Counterparty of its warranties, indemnification obligations, or liability for latent defects.")

    # 6. Article 3: Obligations of the Parties
    pdf.article_heading("3", "Obligations of the Parties")
    pdf.section_heading("3.1", "Company Obligations")
    pdf.body_text("The Company shall: (a) provide the Counterparty with all necessary information, access, and cooperation reasonably required for the performance of the Services; (b) designate a representative who shall be the primary point of contact for all matters relating to this Agreement; (c) review and provide feedback on all deliverables within the timeframes specified herein or as otherwise agreed by the Parties; (d) make timely payments in accordance with the payment terms set forth in Article 5; (e) comply with all Applicable Laws in its use of the Services and deliverables; and (f) not use the Services or deliverables for any unlawful purpose or in any manner inconsistent with this Agreement.")
    pdf.section_heading("3.2", "Counterparty Obligations")
    pdf.body_text("The Counterparty shall: (a) perform the Services in a professional and workmanlike manner, in accordance with industry standards and best practices; (b) comply with all Applicable Laws, the Company's policies and procedures, and any directions reasonably given by the Company's designated representative; (c) maintain accurate and complete records of all work performed and expenses incurred; (d) promptly notify the Company of any issues, delays, or risks that could affect the timely or satisfactory performance of the Services; (e) ensure that all personnel assigned to perform the Services are suitably qualified, trained, and experienced; and (f) cooperate fully with the Company in any audits, reviews, or inspections relating to the performance of the Services.")
    pdf.section_heading("3.3", "Performance Standards")
    pdf.body_text("The Counterparty shall perform the Services in accordance with the performance standards, service levels, and quality metrics specified in Schedule A. Failure to meet such standards shall constitute a material breach of this Agreement, entitling the Company to exercise its remedies under Article 4, including but not limited to termination for cause, reduction of fees, and claims for damages.")
    pdf.section_heading("3.4", "Subcontracting")
    pdf.body_text("The Counterparty shall not subcontract, delegate, or assign any of its obligations under this Agreement to any Third Party without the prior written consent of the Company. Any permitted subcontractor shall be bound by the terms of this Agreement, and the Counterparty shall remain fully liable for the acts and omissions of any subcontractor. The Counterparty shall provide the Company with the names, qualifications, and background information of all subcontractors and shall ensure that all subcontractors comply with the Company's security, confidentiality, and compliance requirements.")
    pdf.section_heading("3.5", "Personnel")
    pdf.body_text("The Counterparty shall assign suitably qualified, experienced, and trained personnel to perform the Services. The Counterparty shall not remove or replace any key personnel without the Company's prior written consent, except in cases of resignation, termination for cause, illness, or other circumstances beyond the Counterparty's reasonable control. In such cases, the Counterparty shall promptly notify the Company and shall propose a replacement of comparable or superior qualifications and experience. The Company shall have the right to interview and approve any replacement personnel.")

    # 7. Article 4: Term and Termination
    pdf.article_heading("4", "Term and Termination")
    pdf.section_heading("4.1", "Term")
    pdf.body_text("This Agreement shall commence on the Effective Date and shall continue for the initial term specified in the recitals above, unless earlier terminated in accordance with this Article 4. Thereafter, this Agreement shall automatically renew for successive one (1) year periods unless either Party gives written notice of non-renewal at least ninety (90) days prior to the expiration of the then-current term.")
    pdf.section_heading("4.2", "Termination for Convenience")
    pdf.body_text("Either Party may terminate this Agreement for convenience upon ninety (90) days' prior written notice to the other Party. In the event of termination for convenience by the Company, the Company shall pay the Counterparty for all Services performed and expenses incurred up to the effective date of termination. In the event of termination for convenience by the Counterparty, the Counterparty shall complete all work in progress and transition all materials and knowledge to the Company.")
    pdf.section_heading("4.3", "Termination for Cause")
    pdf.body_text("Either Party may terminate this Agreement for cause upon thirty (30) days' prior written notice to the other Party, specifying the breach, if the other Party materially breaches any provision of this Agreement and fails to cure such breach within such thirty (30) day period. Immediate termination for cause shall be permitted in the event of: (a) insolvency, bankruptcy, or winding up of the other Party; (b) assignment of the other Party's assets for the benefit of creditors; (c) attachment or seizure of a substantial portion of the other Party's assets; or (d) commission of fraud, wilful misconduct, or gross negligence by the other Party.")
    pdf.section_heading("4.4", "Effects of Termination")
    pdf.body_text("Upon expiration or termination of this Agreement for any reason: (a) all rights and licences granted by either Party to the other Party shall immediately terminate; (b) the Counterparty shall immediately cease all performance of the Services; (c) the Counterparty shall return or destroy all Confidential Information of the Company and provide written certification of such destruction; (d) the Company shall pay the Counterparty for all undisputed Services performed and expenses incurred up to the effective date of termination; (e) the Counterparty shall cooperate with the Company in transitioning the Services to the Company or a replacement vendor; and (f) all provisions that by their nature should survive termination shall survive in accordance with Section 12.10.")

    # 8. Article 5: Compensation and Payment
    pdf.article_heading("5", "Compensation and Payment")
    pdf.section_heading("5.1", "Fees")
    pdf.body_text("In consideration for the Services, the Company shall pay the Counterparty the fees set forth in the Statement of Work or as otherwise agreed in writing by the Parties. All fees are exclusive of applicable taxes, including but not limited to Goods and Services Tax (GST), which shall be borne by the Company in addition to the fees.")
    pdf.section_heading("5.2", "Invoicing")
    pdf.body_text("The Counterparty shall submit invoices to the Company on a monthly basis, within five (5) Business Days of the end of each month. Each invoice shall include: (a) a detailed description of the Services performed; (b) the number of hours worked and the applicable hourly rates, or the fixed fee for milestone deliverables; (c) itemised expenses incurred with supporting documentation; and (d) the applicable GST registration number and tax amounts.")
    pdf.section_heading("5.3", "Payment Terms")
    pdf.body_text("The Company shall pay all properly submitted invoices within thirty (30) days of receipt. Late payments shall incur interest at the rate of one and one-half percent (1.5%) per month, or the maximum rate permitted by Applicable Law, whichever is lower. The Company may dispute any invoice in good faith by providing written notice to the Counterparty within fifteen (15) days of receipt, specifying the basis for the dispute. The Parties shall cooperate in good faith to resolve any disputed amounts promptly.")
    pdf.section_heading("5.4", "Set-off and Deduction")
    pdf.body_text("The Company shall have the right to set off against any amounts payable to the Counterparty under this Agreement any amounts owed by the Counterparty to the Company, including but not limited to damages, liquidated damages, or other claims arising from the Counterparty's breach of this Agreement.")
    pdf.section_heading("5.5", "Audit Rights")
    pdf.body_text("The Company shall have the right, upon reasonable notice and no more than once per calendar year, to audit the Counterparty's records relating to the Services and fees charged hereunder. Such audit shall be conducted during normal business hours and at the Company's expense, unless the audit reveals an overcharge of more than five percent (5%), in which case the Counterparty shall bear the cost of the audit and shall promptly refund the overcharged amount with interest.")
    pdf.section_heading("5.6", "Taxes")
    pdf.body_text("All fees and other amounts payable under this Agreement are exclusive of all applicable taxes, duties, levies, and other governmental charges, including but not limited to GST, VAT, sales tax, use tax, excise tax, and customs duties. The Company shall be responsible for payment of all such taxes, except for taxes based on the Counterparty's net income. The Counterparty shall provide the Company with valid tax invoices and shall cooperate with the Company in claiming any available tax exemptions, credits, or refunds. If any withholding taxes are required by Applicable Law, the Company shall withhold such taxes from payments due to the Counterparty and shall remit such taxes to the applicable taxing authority. The Company shall provide the Counterparty with evidence of such withholding and remittance.")
    pdf.section_heading("5.7", "Travel and Expenses")
    pdf.body_text("All reasonable and necessary travel expenses incurred by the Counterparty's personnel in connection with the performance of the Services shall be reimbursable by the Company, subject to the Company's travel and expense policies and prior written approval for any individual expense exceeding INR 25,000. All expense reimbursements shall be supported by original receipts and detailed expense reports. The Counterparty shall obtain the Company's prior written approval for any travel outside India.")

    # 9. Article 6: Confidentiality and Data Protection
    pdf.article_heading("6", "Confidentiality and Data Protection")
    pdf.section_heading("6.1", "Confidentiality Obligations")
    pdf.body_text("Each Party agrees to hold all Confidential Information of the other Party in strict confidence and not to disclose such Confidential Information to any Third Party without the prior written consent of the Disclosing Party, except as expressly permitted herein. The Receiving Party shall use the Confidential Information solely for the purpose of exercising its rights and performing its obligations under this Agreement. The Receiving Party shall protect the Confidential Information with at least the same degree of care it uses to protect its own confidential information of like importance, but in no event less than reasonable care.")
    pdf.section_heading("6.2", "Permitted Disclosures")
    pdf.body_text("The Receiving Party may disclose Confidential Information to its employees, contractors, and advisors who have a need to know such information for the purpose of performing obligations or exercising rights under this Agreement, provided that such persons are bound by confidentiality obligations no less protective than those set forth herein. The Receiving Party may also disclose Confidential Information as required by Applicable Law, regulation, or court order, provided that the Receiving Party gives the Disclosing Party prompt written notice of such requirement (to the extent permitted by law) and cooperates with the Disclosing Party in seeking a protective order or other appropriate remedy.")
    pdf.section_heading("6.3", "Data Protection")
    pdf.body_text("The Counterparty shall process all Personal Data in accordance with the Digital Personal Data Protection Act, 2023, and all other Applicable Laws relating to data protection and privacy. The Counterparty shall implement and maintain appropriate technical and organisational security measures as specified in Schedule C. The Counterparty shall not process Personal Data for any purpose other than as necessary to perform its obligations under this Agreement, and shall not transfer Personal Data outside India without the Company's prior written consent and compliance with all Applicable Laws.")
    pdf.section_heading("6.4", "Return of Confidential Information")
    pdf.body_text("Upon expiration or termination of this Agreement, or upon the Disclosing Party's written request, the Receiving Party shall promptly return or destroy all Confidential Information of the Disclosing Party and provide written certification of such destruction, except for copies retained in accordance with standard backup and archival procedures or as required by Applicable Law.")
    pdf.section_heading("6.5", "Survival")
    pdf.body_text("The obligations set forth in this Article 6 shall survive the expiration or termination of this Agreement for a period of five (5) years, or, with respect to trade secrets, for so long as such information remains a trade secret under Applicable Law.")
    pdf.section_heading("6.6", "Publicity and References")
    pdf.body_text("Neither Party shall use the other Party's name, logo, trademarks, or other identifying information in any press release, marketing materials, case studies, customer lists, or other public announcements without the prior written consent of the other Party, except as required by Applicable Law or the rules of any stock exchange on which the Party's securities are listed. Notwithstanding the foregoing, the Counterparty may include the Company's name in its customer list and portfolio, subject to the Company's prior written approval of any specific use. The Counterparty shall promptly remove the Company's name from any public materials upon the Company's written request.")

    # 10. Article 7: Intellectual Property
    pdf.article_heading("7", "Intellectual Property Rights")
    pdf.section_heading("7.1", "Company IP")
    pdf.body_text("All Intellectual Property Rights in and to the Company's existing technology, software, data, trademarks, and other materials shall remain the exclusive property of the Company. The Counterparty shall not acquire any right, title, or interest in any Company IP except as expressly granted herein.")
    pdf.section_heading("7.2", "Counterparty IP")
    pdf.body_text("All Intellectual Property Rights in and to the Counterparty's pre-existing technology, software, tools, methodologies, and other materials shall remain the exclusive property of the Counterparty. The Company shall not acquire any right, title, or interest in any Counterparty IP except as expressly granted herein.")
    pdf.section_heading("7.3", "Work Product")
    pdf.body_text("All work product, deliverables, inventions, discoveries, improvements, and modifications created or developed by the Counterparty in the performance of the Services, whether or not patentable, copyrightable, or otherwise protectable ('Work Product'), shall be the sole and exclusive property of the Company. The Counterparty hereby irrevocably assigns to the Company all right, title, and interest in and to the Work Product, including all Intellectual Property Rights therein. The Counterparty shall execute all documents and take all actions reasonably requested by the Company to perfect the Company's ownership of the Work Product.")
    pdf.section_heading("7.4", "Licence Grants")
    pdf.body_text("The Counterparty hereby grants to the Company a perpetual, irrevocable, worldwide, royalty-free, fully paid-up, non-exclusive licence, with the right to sublicense through multiple tiers, to use, reproduce, modify, adapt, publish, translate, create derivative works from, distribute, perform, and display the Counterparty's pre-existing technology and tools to the extent incorporated into the Work Product. The Company hereby grants to the Counterparty a limited, non-exclusive, non-transferable, royalty-free licence to use the Company's IP solely as necessary to perform the Services during the Term.")
    pdf.section_heading("7.5", "Moral Rights")
    pdf.body_text("To the extent permitted by Applicable Law, the Counterparty hereby waives any moral rights or droit moral that it may have in the Work Product, and agrees not to institute, support, maintain, or permit any action or claim on the grounds that any use of the Work Product infringes the Counterparty's moral rights.")

    # 11. Article 8: Representations and Warranties
    pdf.article_heading("8", "Representations and Warranties")
    for num, title, text in _representations_warranties():
        pdf.section_heading(num, title)
        pdf.body_text(text)

    # 12. Article 9: Indemnification
    pdf.article_heading("9", "Indemnification and Limitation of Liability")
    pdf.section_heading("9.1", "Indemnification by Counterparty")
    pdf.body_text("The Counterparty shall indemnify, defend, and hold harmless the Company and its Affiliates, officers, directors, employees, agents, and representatives from and against any and all claims, damages, losses, liabilities, costs, and expenses (including reasonable attorneys' fees) arising out of or relating to: (a) the Counterparty's breach of any representation, warranty, or obligation under this Agreement; (b) the Counterparty's negligence or wilful misconduct; (c) any claim that the Services or deliverables infringe or misappropriate the Intellectual Property Rights of any Third Party; (d) any claim by a Third Party arising from the Counterparty's employment practices, tax obligations, or regulatory compliance; or (e) any Data Breach or other security incident caused by the Counterparty's acts or omissions.")
    pdf.section_heading("9.2", "Indemnification by Company")
    pdf.body_text("The Company shall indemnify, defend, and hold harmless the Counterparty from and against any and all claims, damages, losses, liabilities, costs, and expenses (including reasonable attorneys' fees) arising out of or relating to: (a) the Company's breach of any representation, warranty, or obligation under this Agreement; (b) the Company's negligence or wilful misconduct; or (c) any claim that the Company's materials, data, or instructions furnished to the Counterparty infringe or misappropriate the Intellectual Property Rights of any Third Party.")
    pdf.section_heading("9.3", "Indemnification Procedure")
    pdf.body_text("The indemnified Party shall promptly notify the indemnifying Party in writing of any claim for which indemnification is sought, cooperate reasonably with the indemnifying Party in the defence of such claim, and allow the indemnifying Party to control the defence and settlement thereof. The indemnifying Party shall not settle any claim in a manner that adversely affects the indemnified Party's rights without the indemnified Party's prior written consent, which shall not be unreasonably withheld or delayed.")
    pdf.section_heading("9.4", "Limitation of Liability")
    pdf.body_text("EXCEPT FOR BREACHES OF ARTICLE 6 (CONFIDENTIALITY), ARTICLE 7 (INTELLECTUAL PROPERTY), OR A PARTY'S INDEMNIFICATION OBLIGATIONS UNDER SECTION 9.1 OR 9.2, IN NO EVENT SHALL EITHER PARTY BE LIABLE TO THE OTHER PARTY FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, PUNITIVE, OR EXEMPLARY DAMAGES, INCLUDING BUT NOT LIMITED TO LOSS OF PROFITS, LOSS OF REVENUE, LOSS OF DATA, LOSS OF GOODWILL, BUSINESS INTERRUPTION, OR COST OF SUBSTITUTE SERVICES, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES. THE TOTAL AGGREGATE LIABILITY OF EITHER PARTY UNDER THIS AGREEMENT SHALL NOT EXCEED THE TOTAL AMOUNT PAID OR PAYABLE BY THE COMPANY TO THE COUNTERPARTY UNDER THIS AGREEMENT IN THE TWELVE (12) MONTHS PRECEDING THE EVENT GIVING RISE TO LIABILITY, EXCEPT THAT SUCH CAP SHALL NOT APPLY TO CLAIMS ARISING FROM FRAUD, GROSS NEGLIGENCE, WILFUL MISCONDUCT, OR BREACH OF CONFIDENTIALITY OR INTELLECTUAL PROPERTY OBLIGATIONS.")

    # 13. Article 10: Force Majeure
    pdf.article_heading("10", "Force Majeure")
    for num, title, text in _force_majeure():
        pdf.section_heading(num, title)
        pdf.body_text(text)

    # 14. Article 11: Dispute Resolution
    pdf.article_heading("11", "Dispute Resolution")
    for num, title, text in _dispute_resolution():
        pdf.section_heading(num, title)
        pdf.body_text(text)

    # 15. Article 12: General Provisions
    pdf.article_heading("12", "General Provisions")
    for num, title, text in _general_provisions():
        pdf.section_heading(num, title)
        pdf.body_text(text)

    # 16. Article 13: Compliance and Regulatory Requirements
    pdf.article_heading("13", "Compliance and Regulatory Requirements")
    pdf.section_heading("13.1", "Regulatory Compliance")
    pdf.body_text("The Counterparty shall comply with all Applicable Laws, regulations, and industry standards applicable to the Services, including but not limited to the Indian Contract Act, 1872, the Information Technology Act, 2000 (and rules thereunder), the Digital Personal Data Protection Act, 2023, the Arbitration and Conciliation Act, 1996, the Copyright Act, 1957, the Patents Act, 1970, the Trade Marks Act, 1999, the Goods and Services Tax Act, 2017, the Income Tax Act, 1961, the Companies Act, 2013, the Insolvency and Bankruptcy Code, 2016, the Competition Act, 2002, the Foreign Exchange Management Act, 1999, and all other applicable central, state, and local laws, ordinances, regulations, and codes. The Counterparty shall obtain and maintain all necessary licences, permits, registrations, and approvals required for the performance of the Services.")
    pdf.section_heading("13.2", "Environmental Compliance")
    pdf.body_text("The Counterparty shall comply with all applicable environmental laws and regulations, including but not limited to the Environment (Protection) Act, 1986, the Water (Prevention and Control of Pollution) Act, 1974, the Air (Prevention and Control of Pollution) Act, 1981, and the Hazardous Waste (Management, Handling and Transboundary Movement) Rules, 2008. The Counterparty shall maintain all necessary environmental clearances and shall not engage in any activity that causes or is likely to cause environmental damage.")
    pdf.section_heading("13.3", "Labour Compliance")
    pdf.body_text("The Counterparty shall comply with all applicable labour laws, including but not limited to the Industrial Disputes Act, 1947, the Factories Act, 1948, the Minimum Wages Act, 1948, the Payment of Wages Act, 1936, the Payment of Bonus Act, 1965, the Employees' Provident Funds and Miscellaneous Provisions Act, 1952, the Employees' State Insurance Act, 1948, the Maternity Benefit Act, 1961, the Equal Remuneration Act, 1976, the Child Labour (Prohibition and Regulation) Act, 1986, the Contract Labour (Regulation and Abolition) Act, 1970, the Payment of Gratuity Act, 1972, the Industrial Employment (Standing Orders) Act, 1946, and the Building and Other Construction Workers (Regulation of Employment and Conditions of Service) Act, 1996. The Counterparty shall maintain all necessary registrations and shall promptly notify the Company of any labour disputes, strikes, or lockouts.")
    pdf.section_heading("13.4", "Tax Compliance")
    pdf.body_text("The Counterparty shall be solely responsible for payment of all taxes, duties, levies, and other governmental charges arising from or in connection with the Services, including but not limited to income tax, goods and services tax (GST), professional tax, and any other applicable taxes. The Counterparty shall provide the Company with valid GST invoices and shall maintain accurate and complete tax records. The Counterparty shall indemnify and hold harmless the Company from any claims, liabilities, or penalties arising from the Counterparty's failure to comply with applicable tax laws.")
    pdf.section_heading("13.5", "Audit and Inspection")
    pdf.body_text("The Company shall have the right, upon reasonable notice and no more than twice per calendar year, to audit the Counterparty's compliance with the requirements of this Article 13. Such audit may include review of licences, permits, registrations, tax records, labour records, environmental clearances, and other compliance documentation. The Counterparty shall provide full cooperation and access to all relevant records and personnel. The costs of such audit shall be borne by the Company, unless the audit reveals material non-compliance, in which case the Counterparty shall bear the costs of the audit.")

    # 17. Article 14: Insurance and Risk Management
    pdf.article_heading("14", "Insurance and Risk Management")
    pdf.section_heading("14.1", "Insurance Requirements")
    pdf.body_text("The Counterparty shall maintain, at its own expense, throughout the Term and for a period of three (3) years thereafter, the following insurance coverage with insurers having a minimum credit rating of A- by Standard and Poor's or an equivalent rating by another internationally recognised rating agency: (a) Comprehensive General Liability Insurance with minimum coverage of INR 5,00,00,000 (Rupees Five Crores) per occurrence and INR 10,00,00,000 (Rupees Ten Crores) in aggregate; (b) Professional Indemnity and Errors and Omissions Insurance with minimum coverage of INR 5,00,00,000 (Rupees Five Crores) per claim and in aggregate; (c) Cyber Liability and Data Breach Insurance with minimum coverage of INR 10,00,00,000 (Rupees Ten Crores) per claim and in aggregate; (d) Directors and Officers Liability Insurance with minimum coverage of INR 2,50,00,000 (Rupees Two Crores and Fifty Lakhs); and (e) Workers' Compensation and Employers' Liability Insurance as required by Applicable Law.")
    pdf.section_heading("14.2", "Certificates of Insurance")
    pdf.body_text("The Counterparty shall provide the Company with certificates of insurance evidencing the coverage required herein within fifteen (15) days of the Effective Date and annually thereafter, or upon request by the Company. Such certificates shall name the Company as an additional insured on all liability policies and shall provide for thirty (30) days' prior written notice to the Company of any cancellation, non-renewal, or material change in coverage.")
    pdf.section_heading("14.3", "Risk Management")
    pdf.body_text("The Counterparty shall implement and maintain a comprehensive risk management programme, including but not limited to: (a) regular risk assessments and vulnerability analyses; (b) business continuity and disaster recovery plans tested at least annually; (c) incident response plans for security breaches, data breaches, and other emergency situations; (d) employee training on security awareness, data protection, and compliance obligations; and (e) periodic third-party security audits and penetration testing. The Counterparty shall promptly notify the Company of any material security incident or risk that could affect the Services or the Company's operations.")
    pdf.section_heading("14.4", "Subcontractor Insurance")
    pdf.body_text("The Counterparty shall ensure that all subcontractors and sub-processors engaged in the performance of the Services maintain insurance coverage substantially similar to that required of the Counterparty under this Article 14. The Counterparty shall provide the Company with certificates of insurance for all subcontractors upon request.")

    # 18. Article 15: Records and Reporting
    pdf.article_heading("15", "Records and Reporting")
    pdf.section_heading("15.1", "Record Keeping")
    pdf.body_text("The Counterparty shall maintain accurate, complete, and detailed records of all work performed, expenses incurred, and time spent in connection with the Services, including but not limited to: (a) timesheets and attendance records for all personnel assigned to the project; (b) invoices, receipts, and supporting documentation for all expenses; (c) project plans, status reports, and meeting minutes; (d) design documents, technical specifications, and test results; (e) change requests and impact assessments; and (f) correspondence and communications with the Company. Such records shall be retained for a period of not less than seven (7) years from the date of creation or the date of termination of this Agreement, whichever is later.")
    pdf.section_heading("15.2", "Progress Reports")
    pdf.body_text("The Counterparty shall provide the Company with written progress reports on a weekly basis (or as otherwise specified in the Statement of Work) describing: (a) work completed during the reporting period; (b) work planned for the next reporting period; (c) any issues, risks, or delays encountered or anticipated; (d) any changes to the project plan, timeline, or budget; and (e) any decisions or approvals required from the Company. The progress reports shall be delivered to the Company's designated representative by email no later than the close of business on the last Business Day of each reporting period.")
    pdf.section_heading("15.3", "Financial Reports")
    pdf.body_text("The Counterparty shall provide the Company with detailed financial reports on a monthly basis, including: (a) a breakdown of fees earned, expenses incurred, and payments received; (b) a comparison of actual costs against budgeted costs, with explanations for any variances exceeding ten percent (10%); (c) a forecast of costs for the remainder of the project; and (d) any outstanding invoices or disputed amounts. The financial reports shall be delivered together with the monthly invoices.")
    pdf.section_heading("15.4", "Audit of Records")
    pdf.body_text("The Company shall have the right, upon reasonable notice and no more than twice per calendar year, to audit the Counterparty's records relating to the Services. Such audit shall be conducted during normal business hours and at the Company's expense, unless the audit reveals an overcharge or material discrepancy of more than five percent (5%), in which case the Counterparty shall bear the costs of the audit and shall promptly refund any overcharged amounts with interest at the rate specified in Section 5.3.")

    # 19. Schedules
    for sched_title, sched_subtitle, items in _schedules():
        pdf.add_page()
        pdf.set_font("ArialNR", "B", 14)
        pdf.cell(0, 12, sched_title, align="C", **_nx())
        pdf.set_font("ArialNR", "B", 12)
        pdf.cell(0, 8, sched_subtitle, align="C", **_nx())
        pdf.line(25.4, pdf.get_y(), 210 - 25.4, pdf.get_y())
        pdf.ln(5)
        pdf.set_font("TimesNR", "", 11)
        for item in items:
            if item.startswith("     "):
                pdf.set_x(45.4)
                pdf.multi_cell(210 - 45.4 - 25.4, 6, item.strip())
            elif item.startswith("SCHEDULE") or item.startswith("EXHIBIT"):
                pdf.set_font("TimesNR", "B", 11)
                pdf.cell(0, 7, item, **_nx())
                pdf.set_font("TimesNR", "", 11)
            else:
                pdf.multi_cell(210 - 50.8, 6, item)
            pdf.ln(1)

    # 17. Signature Page
    for sched_title, sched_subtitle, items in _signature_page(party1, party2):
        pdf.add_page()
        pdf.set_font("ArialNR", "B", 14)
        pdf.cell(0, 12, sched_title, align="C", **_nx())
        pdf.set_font("ArialNR", "B", 12)
        pdf.cell(0, 8, sched_subtitle, align="C", **_nx())
        pdf.line(25.4, pdf.get_y(), 210 - 25.4, pdf.get_y())
        pdf.ln(10)
        pdf.set_font("TimesNR", "", 11)
        for item in items:
            if item == "":
                pdf.ln(4)
            else:
                pdf.cell(0, 7, item, **_nx())

    pdf.output(output_path)
    return output_path


if __name__ == "__main__":
    path = generate_contract_pdf(
        contract_type="nda",
        title="Mutual NDA - InnoTech Solutions Pvt Ltd",
        party1="Acme Manufacturing Pvt Ltd",
        party2="InnoTech Solutions Pvt Ltd",
        date="15 January 2025",
        parsed_text="This is a test NDA agreement for demonstration purposes.",
        clauses=[],
        output_path="./uploads/demo/test_nda.pdf",
    )
    print(f"Generated: {path}")
