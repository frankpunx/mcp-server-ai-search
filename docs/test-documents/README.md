# Test Documents for Azure AI Search Agentic Retrieval

This directory contains sample documents designed to test the Azure AI Search agentic retrieval capabilities. These documents simulate a realistic enterprise knowledge base with diverse content types.

## Document Inventory

| Document | Type | Size | Topics |
|----------|------|------|--------|
| [hr-policy-handbook.md](hr-policy-handbook.md) | Policy | ~4KB | HR policies, benefits, PTO |
| [product-manual-smartwidget.md](product-manual-smartwidget.md) | Technical | ~8KB | IoT device manual |
| [technical-faq.md](technical-faq.md) | FAQ | ~6KB | IT support Q&A |
| [ai-research-whitepaper.md](ai-research-whitepaper.md) | Research | ~10KB | AI/ML technical paper |
| [quarterly-report-q3-2025.md](quarterly-report-q3-2025.md) | Financial | ~6KB | Financial report |

---

## Document Descriptions

### 1. HR Policy Handbook (`hr-policy-handbook.md`)

**Purpose**: Simulates an employee handbook with company policies.

**Content Sections**:
- Time Off and Leave Policies (PTO, sick leave, parental leave, bereavement)
- Remote Work Policy (hybrid model, equipment, requirements)
- Compensation and Benefits (health insurance, 401k, professional development)
- Code of Conduct (workplace behavior, conflicts of interest, social media)
- Performance Management (reviews, ratings, promotions)

**Test Queries**:
| Query Type | Example Query | Expected Answer Source |
|------------|---------------|----------------------|
| Factual | "How many PTO days do new employees get?" | Section 2.1 - 15 days |
| Factual | "What is the 401k match?" | Section 4.3 - 100% up to 4%, 50% on next 2% |
| Procedural | "How do I request time off?" | Section 2.1 - Submit 2 weeks in advance |
| Comparative | "What are the health insurance options?" | Section 4.2 - Basic, Standard, Premium plans |
| Policy | "Can I work from home?" | Section 3.1 - Hybrid model, 2 days in office |

---

### 2. SmartWidget Pro 3000 Manual (`product-manual-smartwidget.md`)

**Purpose**: Simulates a consumer electronics product manual.

**Content Sections**:
- Technical Specifications (dimensions, connectivity, power)
- Getting Started (setup, LED indicators)
- Features (voice control, automation, energy monitoring)
- Troubleshooting (connection issues, offline problems, factory reset)
- Advanced Configuration (API access, local mode, Zigbee)
- Safety and Compliance

**Test Queries**:
| Query Type | Example Query | Expected Answer Source |
|------------|---------------|----------------------|
| Troubleshooting | "My SmartWidget won't connect to WiFi" | Section 3.1 - 5 solutions listed |
| Factual | "What do the LED colors mean?" | Section 1.3 - LED status table |
| Procedural | "How do I factory reset the device?" | Section 3.5 - 5-step process |
| Technical | "What's the API endpoint?" | Section 4.1 - api.contoso-smarthome.com/v2 |
| Specification | "What connectivity does it support?" | Specs table - WiFi 6, Bluetooth 5.2, Zigbee 3.0 |

---

### 3. IT Support FAQ (`technical-faq.md`)

**Purpose**: Simulates an IT helpdesk knowledge base.

**Content Sections**:
- Account & Access (password reset, MFA, lockouts, access requests)
- VPN & Remote Access (connection, personal devices, performance)
- Email & Communication (storage limits, out-of-office, recall, attachments)
- Hardware & Software (requests, installation, troubleshooting, printers)
- Data & Security (file sharing, phishing, encryption)

**Test Queries**:
| Query Type | Example Query | Expected Answer Source |
|------------|---------------|----------------------|
| Procedural | "How do I reset my password?" | Account section - 2 methods |
| Troubleshooting | "I'm locked out of my account" | Account section - 3 solutions |
| Factual | "What's the email attachment limit?" | Email section - 25MB external, 150MB internal |
| How-to | "How do I set up MFA?" | Account section - 5-step process |
| Policy | "Can I use VPN on personal device?" | VPN section - Yes with restrictions |

---

### 4. AI Research Whitepaper (`ai-research-whitepaper.md`)

**Purpose**: Simulates a technical research document.

**Content Sections**:
- Evolution of Enterprise Search (3 generations)
- Technical Architecture (knowledge base structure, embeddings, hybrid search)
- Implementation Case Studies (financial, healthcare, manufacturing)
- Best Practices (data preparation, query understanding, evaluation)
- Future Directions (autonomous management, multi-agent, proactive delivery)

**Test Queries**:
| Query Type | Example Query | Expected Answer Source |
|------------|---------------|----------------------|
| Conceptual | "What is agentic retrieval?" | Section 1.2 - Definition and capabilities |
| Technical | "What's the best chunk size for technical docs?" | Section 2.2 - 512 tokens |
| Case Study | "What results did the healthcare case study show?" | Section 3.2 - 78% search time reduction |
| Comparative | "How does semantic search differ from agentic?" | Section 1.1 - Generation 2 vs 3 |
| Recommendation | "What's the recommended hybrid search weighting?" | Section 2.3 - 70/20/10 split |

---

### 5. Q3 2025 Financial Report (`quarterly-report-q3-2025.md`)

**Purpose**: Simulates a corporate financial report.

**Content Sections**:
- Financial Highlights (revenue, earnings, cash position)
- Business Segment Performance (Cloud, Hardware, Services)
- Geographic Performance (by region)
- Operating Expenses (R&D, S&M, G&A breakdown)
- Strategic Initiatives (AI transformation, sustainability, partners)
- Q4 Outlook and Guidance

**Test Queries**:
| Query Type | Example Query | Expected Answer Source |
|------------|---------------|----------------------|
| Numerical | "What was Q3 2025 total revenue?" | Highlights - $4.82B |
| Comparative | "How did Cloud vs Hardware perform?" | Segments - Cloud +28%, Hardware +8% |
| Growth | "What's the fastest growing segment?" | Segments - Cloud Services at 28% YoY |
| Guidance | "What's the Q4 revenue outlook?" | Outlook - $5.05B-$5.15B |
| Strategic | "What is Project Atlas?" | Strategic section - AI Transformation initiative |

---

## Testing Scenarios

### Scenario 1: Simple Factual Retrieval
Test direct fact-finding across different document types.

```
Queries:
- "How many sick days do employees get?" → 10 days (HR handbook)
- "What's the SmartWidget warranty?" → 2 years (Product manual)
- "What's the IT help desk phone number?" → x5555 (IT FAQ)
```

### Scenario 2: Multi-Document Synthesis
Test queries requiring information from multiple documents.

```
Queries:
- "What AI initiatives does Contoso have?" 
  → Combines: Research whitepaper + Financial report Project Atlas
  
- "What technology products does Contoso offer?"
  → Combines: SmartWidget manual + Financial report hardware segment
```

### Scenario 3: Procedural/How-To
Test step-by-step instruction retrieval.

```
Queries:
- "How do I connect the SmartWidget to Alexa?"
- "How do I submit a PTO request?"
- "How do I encrypt an email?"
```

### Scenario 4: Troubleshooting
Test problem-solution matching.

```
Queries:
- "SmartWidget LED is blinking red"
- "VPN is slow"
- "My laptop is running slowly"
```

### Scenario 5: Comparative Analysis
Test queries requiring comparison of options.

```
Queries:
- "Compare the health insurance plans"
- "What's the difference between basic and premium search?"
- "How do regional revenues compare?"
```

### Scenario 6: Numerical/Data Extraction
Test extraction of specific numbers from tables.

```
Queries:
- "What's the Cloud Services ARR?"
- "What's the operating margin?"
- "How much PTO can be carried over?"
```

---

## Upload Instructions

After deploying the Azure infrastructure with `azd up`, upload documents using:

```bash
# Option 1: Use the upload script
uv run python scripts/upload_documents.py

# Option 2: Manual upload via Azure CLI
az storage blob upload-batch \
  --account-name <storage-account> \
  --destination documents \
  --source docs/test-documents \
  --auth-mode login
```

Then trigger the indexer:
```bash
az search indexer run \
  --name documents-indexer \
  --service-name <search-service> \
  --resource-group <resource-group>
```

---

## Expected Indexer Behavior

The Azure AI Search indexer will:

1. **Extract text** from markdown files
2. **Chunk documents** into smaller segments for retrieval
3. **Generate embeddings** using the configured OpenAI model
4. **Apply skillset** for AI enrichment
5. **Populate index** with searchable content
6. **Update Knowledge Base** for agentic retrieval

**Estimated Processing Time**: 2-5 minutes for these 5 documents

---

## Validation Checklist

After indexing completes, verify:

- [ ] Index contains 5+ documents (one per file, may be chunked)
- [ ] Embeddings are generated (vector field populated)
- [ ] Knowledge Base is queryable
- [ ] Sample queries return relevant results
- [ ] Citations point to correct source documents

---

*Last updated: December 2025*
