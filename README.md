# AI Invoice Data Extractor

A sophisticated invoice processing system that extracts structured data from invoices using LLMs and vector indexing.

## Core Features

### 1. Multi-Model Support
- OpenAI GPT-4 Turbo
- Google Gemini 1.5 Flash
- Configurable parameters
- Temperature and token control

### 2. Document Processing
- LlamaParse integration
- Vector indexing with LlamaIndex
- Chunk-based processing
- Markdown output format

### 3. Data Extraction Pipeline

#### Document Parsing
- PDF parsing
- Text extraction
- Structure preservation
- Format conversion

#### Data Processing
- Invoice field identification
- Item extraction
- Amount calculation
- Tax computation

#### Output Generation
- DataFrame creation
- Excel report generation
- Structured data output
- Download options

### 4. Extracted Data Fields

- Invoice Number
- Date
- Customer Name
- Item Details:
  - Names
  - Descriptions
  - Quantities
  - Individual Amounts
- Tax Information
- Total Amount

## Technical Implementation

### 1. Vector Store Setup
- Chunk size: 512 tokens
- BGE embeddings
- Query engine configuration

### 2. Data Processing Flow
- File upload handling
- Async processing
- Temporary storage
- Cleanup routines

### 3. Output Generation
- DataFrame structuring
- Excel formatting
- Table display
- Download preparation

## Features

### 1. Input Support
- Multiple file upload
- PDF format support
- Batch processing
- Progress tracking

### 2. Data Extraction
- Automated field detection
- Item categorization
- Amount calculation
- Tax computation

### 3. Output Options
- Interactive table view
- Excel download
- Structured format
- Multiple invoice handling


## Best Practices

1. Document Preparation
   - Clear PDF formatting
   - Standard invoice layout
   - Readable text
   - Consistent structure

2. Processing Configuration
   - Appropriate chunk size
   - Model selection
   - Temperature setting
   - Token limits

3. Output Management
   - Regular downloads
   - Data verification
   - Format checking
   - Backup creation
