import PyPDF2
import fitz  # PyMuPDF
import re
import json
from typing import Dict, List, Tuple
import statistics
from collections import Counter
import nltk
from nltk.corpus import stopwords

class PDFStructureExtractor:
    def __init__(self):
        try:
            self.stop_words = set(stopwords.words('english'))
        except LookupError:
            # If stopwords not available, use empty set
            self.stop_words = set()
        
    def extract_structure(self, pdf_path: str) -> Dict:
        """
        Main function to extract title and heading structure from PDF
        """
        try:
            # Open PDF with PyMuPDF for better font and formatting analysis
            doc = fitz.open(pdf_path)
            
            # Extract text with formatting information
            pages_data = []
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                blocks = page.get_text("dict")
                pages_data.append({
                    'page_num': page_num + 1,
                    'blocks': blocks,
                    'text_lines': self._extract_formatted_lines(blocks)
                })
            
            doc.close()
            
            # Analyze font characteristics across the document
            font_stats = self._analyze_font_characteristics(pages_data)
            
            # Extract title from first page with improved logic
            title = self._extract_title_improved(pages_data[0], font_stats)
            
            # Extract headings with improved filtering
            outline = self._extract_headings_improved(pages_data, font_stats)
            
            return {
                "title": title,
                "outline": outline
            }
            
        except Exception as e:
            print(f"Error in extract_structure: {str(e)}")
            return {
                "title": "Error extracting title",
                "outline": []
            }
    
    def _extract_formatted_lines(self, blocks: Dict) -> List[Dict]:
        """Extract text lines with formatting information"""
        lines = []
        
        for block in blocks.get('blocks', []):
            if block.get('type') == 0:  # Text block
                for line in block.get('lines', []):
                    line_text = ""
                    font_sizes = []
                    font_flags = []
                    font_names = []
                    
                    for span in line.get('spans', []):
                        line_text += span.get('text', '')
                        font_sizes.append(span.get('size', 12))
                        font_flags.append(span.get('flags', 0))
                        font_names.append(span.get('font', ''))
                    
                    if line_text.strip():
                        avg_size = statistics.mean(font_sizes) if font_sizes else 12
                        lines.append({
                            'text': line_text.strip(),
                            'bbox': line.get('bbox', [0, 0, 0, 0]),
                            'font_sizes': font_sizes,
                            'font_flags': font_flags,
                            'font_names': font_names,
                            'avg_font_size': avg_size,
                            'max_font_size': max(font_sizes) if font_sizes else 12,
                            'is_bold': any(flag & 2**4 for flag in font_flags),
                            'is_italic': any(flag & 2**6 for flag in font_flags)
                        })
        
        return lines
    
    def _analyze_font_characteristics(self, pages_data: List[Dict]) -> Dict:
        """Analyze font characteristics to identify body text and heading patterns"""
        all_font_sizes = []
        all_lines = []
        
        for page_data in pages_data:
            for line in page_data['text_lines']:
                # Skip very short lines and likely non-content
                if len(line['text'].strip()) > 3:
                    all_font_sizes.append(line['avg_font_size'])
                    all_lines.append(line)
        
        # Find the most common font size (body text)
        font_size_counter = Counter([round(size, 1) for size in all_font_sizes])
        body_font_size = font_size_counter.most_common(1)[0][0] if font_size_counter else 12.0
        
        # Get unique font sizes sorted by frequency and size
        unique_sizes = sorted(set([round(size, 1) for size in all_font_sizes]), reverse=True)
        
        # Calculate significant size differences for heading detection
        size_threshold = body_font_size + 0.5  # More sensitive threshold
        
        return {
            'body_font_size': body_font_size,
            'size_threshold': size_threshold,
            'unique_sizes': unique_sizes,
            'all_lines': all_lines
        }
    
    def _extract_title_improved(self, first_page_data: Dict, font_stats: Dict) -> str:
        """Extract document title with improved logic"""
        lines = first_page_data['text_lines']
        
        # Look for title candidates in first 10 lines
        title_candidates = []
        
        for i, line in enumerate(lines[:10]):
            text = line['text'].strip()
            
            # Skip obvious non-titles
            if (not text or 
                len(text) < 3 or 
                text.isdigit() or 
                'copyright' in text.lower() or
                'version' in text.lower() or
                '©' in text or
                'page' in text.lower() and text.lower().count('page') > 0):
                continue
            
            # Calculate title score
            score = 0
            
            # Font size bonus
            if line['avg_font_size'] > font_stats['body_font_size']:
                score += (line['avg_font_size'] - font_stats['body_font_size']) * 5
            
            # Bold text bonus
            if line['is_bold']:
                score += 10
            
            # Position preference (earlier is better, but not too early)
            if 0 <= i <= 5:
                score += 15 - (i * 2)
            
            # Length preference
            word_count = len(text.split())
            if 2 <= word_count <= 6:
                score += 15
            elif word_count == 1:
                score += 5
            
            # Special bonus for title-like phrases
            if any(phrase in text.lower() for phrase in ['overview', 'foundation', 'extension', 'level', 'introduction', 'guide', 'manual']):
                score += 20
            
            title_candidates.append((score, text, i))
        
        # Sort by score and get best candidate
        title_candidates.sort(key=lambda x: x[0], reverse=True)
        
        if title_candidates:
            # Try to combine related title parts
            best_candidate = title_candidates[0]
            title_text = best_candidate[1]
            
            # Look for additional title parts in nearby lines
            best_line_idx = best_candidate[2]
            combined_title_parts = [title_text]
            
            # Check line before and after for related content
            for offset in [-1, 1]:
                check_idx = best_line_idx + offset
                if 0 <= check_idx < len(lines):
                    check_line = lines[check_idx]
                    check_text = check_line['text'].strip()
                    
                    # If it's a related title part (similar font size, contains key words)
                    if (check_text and 
                        abs(check_line['avg_font_size'] - lines[best_line_idx]['avg_font_size']) < 2 and
                        any(word in check_text.lower() for word in ['overview', 'foundation', 'extension', 'level', 'introduction', 'guide', 'manual']) and
                        len(check_text.split()) <= 8):
                        
                        if offset == -1:
                            combined_title_parts.insert(0, check_text)
                        else:
                            combined_title_parts.append(check_text)
            
            # Combine title parts
            final_title = ' '.join(combined_title_parts)
            
            return final_title.strip()
        
        return "Document Title"
    
    def _extract_headings_improved(self, pages_data: List[Dict], font_stats: Dict) -> List[Dict]:
        """Extract headings with improved filtering"""
        headings = []
        body_size = font_stats['body_font_size']
        
        # Define heading patterns
        heading_patterns = [
            r'^(Revision History)\s*$',
            r'^(Table of Contents)\s*$', 
            r'^(Acknowledgements)\s*$',
            r'^(Abstract)\s*$',
            r'^(Introduction)\s*$',
            r'^(Conclusion)\s*$',
            r'^(Summary)\s*$',
            r'^(References)\s*$',
            r'^(Bibliography)\s*$',
            r'^(Appendix)\s*$',
            r'^\d+\.\s+[A-Z][^.]*$',  # "1. Introduction to..." 
            r'^\d+\.\d+\s+[A-Z][^.]*$',  # "2.1 Intended Audience"
            r'^\d+\s+(References)\s*$',  # "4. References"
            r'^Chapter\s+\d+',  # Chapter headings
            r'^Section\s+\d+',  # Section headings
        ]
        
        for page_data in pages_data:
            page_num = page_data['page_num']
            
            for line in page_data['text_lines']:
                text = line['text'].strip()
                
                # Skip obvious non-headings
                if not self._is_valid_heading_candidate(text, line, body_size):
                    continue
                
                # Check against patterns and font analysis
                heading_level = None
                is_heading = False
                
                # Pattern-based detection
                for pattern in heading_patterns:
                    if re.match(pattern, text, re.IGNORECASE):
                        is_heading = True
                        # Determine level based on pattern
                        if re.match(r'^\d+\.\d+', text):
                            heading_level = "H2"
                        elif re.match(r'^\d+\.', text):
                            heading_level = "H1"
                        else:
                            heading_level = "H1"
                        break
                
                # Font-based detection for headings not caught by patterns
                if not is_heading:
                    # Check if font size significantly larger than body
                    if line['avg_font_size'] > body_size + 2:
                        is_heading = True
                        if line['avg_font_size'] > body_size + 4:
                            heading_level = "H1"
                        else:
                            heading_level = "H2"
                    # Check for bold text with reasonable size increase
                    elif line['is_bold'] and line['avg_font_size'] > body_size + 0.5:
                        # Additional checks for bold headings
                        if (len(text.split()) <= 10 and 
                            not any(word in text.lower() for word in ['the', 'and', 'or', 'but', 'with', 'from']) and
                            text[0].isupper()):
                            is_heading = True
                            heading_level = "H2"
                
                # Add heading if valid
                if is_heading and heading_level:
                    clean_text = self._clean_heading_text(text)
                    
                    # Final validation
                    if (clean_text and 
                        len(clean_text) > 2 and 
                        not self._is_duplicate_heading(clean_text, headings)):
                        
                        headings.append({
                            "level": heading_level,
                            "text": clean_text,
                            "page": page_num
                        })
        
        # Sort by page number and maintain order
        headings.sort(key=lambda x: (x['page'], x['text']))
        
        return headings
    
    def _is_valid_heading_candidate(self, text: str, line: Dict, body_size: float) -> bool:
        """Strict validation for heading candidates"""
        # Length constraints
        if len(text) < 3 or len(text) > 150:
            return False
        
        # Must not be just numbers or contain obvious exclusions
        exclusions = [
            r'^\d+$',  # Just numbers
            r'page\s+\d+',  # Page numbers  
            r'©.*copyright',  # Copyright
            r'www\.',  # URLs
            r'version\s+\d+',  # Version numbers
            r'email|@',  # Email addresses
            r'http[s]?://',  # URLs
        ]
        
        for exclusion in exclusions:
            if re.search(exclusion, text, re.IGNORECASE):
                return False
        
        # Avoid very long sentences that are clearly content
        if len(text.split()) > 15:
            return False
        
        # Avoid text that looks like regular paragraphs
        if (text.lower().count('the ') > 2 or 
            text.lower().count(' and ') > 1 or
            text.endswith('.') and len(text.split()) > 8):
            return False
        
        return True
    
    def _is_duplicate_heading(self, text: str, existing_headings: List[Dict]) -> bool:
        """Check for duplicate headings"""
        return any(h['text'] == text for h in existing_headings)
    
    def _clean_heading_text(self, text: str) -> str:
        """Clean and normalize heading text"""
        # Remove extra whitespace but preserve intentional spacing
        text = ' '.join(text.split())
        
        # Remove trailing periods from obvious headings (but be careful)
        if (len(text.split()) <= 8 and 
            not text.endswith('...') and 
            text.endswith('.') and
            not re.search(r'\w\.\w', text)):  # Don't remove periods from abbreviations
            text = text.rstrip('.')
        
        return text.strip()


def extract_pdf_structure(pdf_path: str) -> Dict:
    """
    Extract title and heading structure from PDF
    """
    try:
        extractor = PDFStructureExtractor()
        result = extractor.extract_structure(pdf_path)
        return result
    
    except Exception as e:
        print(f"Error processing PDF {pdf_path}: {str(e)}")
        return {
            "title": "Error extracting title",
            "outline": []
        }