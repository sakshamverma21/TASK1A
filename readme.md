# Task 1A: PDF Structure Extraction

## Approach

This solution extracts structured outlines from PDF documents by analyzing font characteristics, formatting patterns, and text positioning to identify titles and hierarchical headings.

### Key Components

1. **Font Analysis**: Analyzes font sizes, weights, and styles across the document to establish baseline body text characteristics and identify potential headings.

2. **Title Extraction**: Uses a scoring system that considers:
   - Font size relative to body text
   - Bold formatting
   - Position in document (first page preference)
   - Word count and content patterns
   - Proximity to related title components

3. **Heading Detection**: Employs dual approach:
   - **Pattern-based**: Regex patterns for numbered sections, common headings
   - **Font-based**: Size and formatting analysis relative to body text

4. **Hierarchical Classification**: Determines heading levels (H1, H2, H3) based on:
   - Font size thresholds
   - Numbering patterns (1.0 vs 1.1 vs 1.1.1)
   - Formatting characteristics

## Libraries Used

- **PyMuPDF (fitz)**: Primary PDF processing for detailed font and formatting analysis
- **PyPDF2**: Backup PDF processing capability
- **NLTK**: Natural language processing for stopword filtering
- **Statistics**: Font size analysis and statistical calculations

## Key Features

- Robust font characteristic analysis across entire document
- Multi-pattern heading detection with fallback mechanisms
- Intelligent title extraction with component combination
- Duplicate detection and text cleaning
- Error handling for various PDF formats

## Build and Run Instructions

### Building the Docker Image
```bash
docker build --platform linux/amd64 -t pdf-extractor:task1a .
```

### Running the Solution
```bash
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdf-extractor:task1a
```

The solution automatically processes all PDF files in the `/app/input` directory and generates corresponding JSON files in `/app/output` with the required format:

```json
{
  "title": "Document Title",
  "outline": [
    { "level": "H1", "text": "Introduction", "page": 1 },
    { "level": "H2", "text": "Background", "page": 2 }
  ]
}
```

## Performance Considerations

- Optimized for CPU-only execution
- Efficient memory usage for large documents
- Fast processing through targeted analysis
- No external network dependencies
