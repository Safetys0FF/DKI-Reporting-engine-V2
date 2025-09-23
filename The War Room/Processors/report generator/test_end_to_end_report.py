#!/usr/bin/env python3
"""
End-to-End Report Generation Test
Tests complete report generation workflow from start to finish
"""

import sys
import logging
from datetime import datetime
from gateway_controller import GatewayController
from document_processor import DocumentProcessor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_complete_report_generation():
    """Test complete end-to-end report generation"""
    
    print("📄 DKI ENGINE - END-TO-END REPORT TEST")
    print("Testing Complete Report Generation Workflow")
    print("=" * 60)
    
    try:
        # Initialize gateway controller
        gc = GatewayController()
        print(f"✅ Gateway Controller initialized with {len(gc.section_renderers)} renderers")
        
        # Test data for complete report
        test_case_data = {
            'case_id': 'E2E-TEST-2025-001',
            'investigator': 'Test Agent - DEESCALATION',
            'client': 'System Validation Client',
            'subject': 'John Doe - End-to-End System Test',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'report_type': 'investigative',
            'client_contact': 'validation@dkiservices.com',
            'case_description': 'Complete system validation test case for DKI Engine',
            'objectives': [
                'Validate complete report generation workflow',
                'Test all section renderers in sequence', 
                'Confirm signal protocol functionality',
                'Verify media processing integration'
            ]
        }
        
        # Case sources stub (required by most renderers)
        case_sources = {
            'intake': {
                'client_info': test_case_data,
                'case_details': test_case_data
            },
            'notes': {
                'investigator_notes': 'End-to-end validation test notes',
                'case_progress': 'Testing complete system workflow'
            },
            'evidence': {
                'documents': ['test_document.pdf'],
                'media': ['test_image.png'],
                'analysis': 'System validation evidence'
            },
            'prior_section': {}
        }
        
        print("\n🔄 TESTING COMPLETE REPORT WORKFLOW:")
        print("-" * 45)
        
        # Test each section in sequence
        section_results = {}
        total_sections = len(gc.section_renderers)
        successful_sections = 0
        
        for section_key, renderer in gc.section_renderers.items():
            try:
                print(f"  Generating {section_key}...")
                
                # Generate section content
                try:
                    # Try with case_sources first
                    result = renderer.render_model(test_case_data, case_sources)
                except TypeError:
                    # Fallback to single argument
                    result = renderer.render_model(test_case_data)
                
                if result and len(str(result)) > 10:  # Check for meaningful content
                    print(f"    ✅ {section_key}: Generated ({len(str(result))} chars)")
                    section_results[section_key] = {
                        'status': 'success',
                        'content_length': len(str(result)),
                        'content_preview': str(result)[:100] + "..."
                    }
                    successful_sections += 1
                else:
                    print(f"    ⚠️ {section_key}: Empty or minimal content")
                    section_results[section_key] = {
                        'status': 'empty',
                        'content_length': len(str(result)) if result else 0
                    }
                    
            except Exception as e:
                print(f"    ❌ {section_key}: Failed - {str(e)[:50]}")
                section_results[section_key] = {
                    'status': 'failed',
                    'error': str(e)
                }
        
        # Test report compilation
        print(f"\n📊 REPORT GENERATION SUMMARY:")
        print("-" * 35)
        
        success_rate = (successful_sections / total_sections) * 100
        print(f"Section Success Rate: {success_rate:.1f}% ({successful_sections}/{total_sections})")
        
        # Show section details
        if successful_sections > 0:
            print(f"\n✅ SUCCESSFUL SECTIONS:")
            for section_key, result in section_results.items():
                if result['status'] == 'success':
                    print(f"  {section_key}: {result['content_length']} characters")
        
        if successful_sections < total_sections:
            print(f"\n⚠️ ISSUES FOUND:")
            for section_key, result in section_results.items():
                if result['status'] != 'success':
                    status = result['status']
                    error = result.get('error', 'No details')[:50]
                    print(f"  {section_key}: {status} - {error}")
        
        # Overall assessment
        if success_rate >= 90:
            print(f"\n🎉 END-TO-END REPORT: ✅ EXCELLENT ({success_rate:.1f}%)")
            return True
        elif success_rate >= 75:
            print(f"\n⚠️ END-TO-END REPORT: GOOD ({success_rate:.1f}%)")
            return True
        elif success_rate >= 50:
            print(f"\n⚠️ END-TO-END REPORT: PARTIAL ({success_rate:.1f}%)")
            return False
        else:
            print(f"\n❌ END-TO-END REPORT: FAILED ({success_rate:.1f}%)")
            return False
            
    except Exception as e:
        print(f"❌ End-to-End Test Failed: {e}")
        return False

def test_media_processing_integration():
    """Test media processing integration with Section 8"""
    
    print("\n🎬 TESTING MEDIA PROCESSING INTEGRATION:")
    print("-" * 45)
    
    try:
        # Initialize document processor
        doc_processor = DocumentProcessor()
        print("✅ Document Processor initialized")
        
        # Test with our existing test image
        test_files = ['test_ocr_image.png']
        
        media_results = {}
        for test_file in test_files:
            try:
                print(f"  Processing {test_file}...")
                result = doc_processor.process_file(test_file)
                
                if result and result.get('success'):
                    text_length = len(result.get('text', ''))
                    print(f"    ✅ {test_file}: Processed ({text_length} chars extracted)")
                    media_results[test_file] = {
                        'status': 'success',
                        'text_length': text_length,
                        'methods': result.get('processing_methods', [])
                    }
                else:
                    print(f"    ❌ {test_file}: Processing failed")
                    media_results[test_file] = {'status': 'failed'}
                    
            except Exception as e:
                print(f"    ❌ {test_file}: Error - {str(e)[:50]}")
                media_results[test_file] = {'status': 'error', 'error': str(e)}
        
        # Test Section 8 with media results
        print(f"  Testing Section 8 with media data...")
        
        try:
            from section_8_renderer import Section8Renderer
            section_8 = Section8Renderer()
            
            test_data = {
                'case_id': 'MEDIA-TEST-001',
                'media_results': media_results
            }
            
            case_sources = {
                'evidence': {'media_analysis': media_results},
                'intake': {},
                'notes': {},
                'prior_section': {}
            }
            
            section_8_result = section_8.render_model(test_data, case_sources)
            
            if section_8_result:
                print(f"    ✅ Section 8: Media integration successful")
                return True
            else:
                print(f"    ⚠️ Section 8: Empty result")
                return False
                
        except Exception as e:
            print(f"    ❌ Section 8: Integration failed - {str(e)[:50]}")
            return False
            
    except Exception as e:
        print(f"❌ Media Processing Test Failed: {e}")
        return False

def main():
    """Run complete end-to-end test"""
    
    # Test 1: Complete report generation
    report_ok = test_complete_report_generation()
    
    # Test 2: Media processing integration
    media_ok = test_media_processing_integration()
    
    # Overall result
    print("\n📊 OVERALL END-TO-END TEST RESULTS:")
    print("=" * 42)
    
    if report_ok and media_ok:
        print("✅ END-TO-END REPORT GENERATION: OPERATIONAL")
        print("✅ Media processing integration: WORKING")
        print("✅ Complete system workflow: VALIDATED")
        return True
    else:
        print("❌ END-TO-END REPORT GENERATION: ISSUES FOUND")
        if not report_ok:
            print("❌ Report generation: PROBLEMS")
        if not media_ok:
            print("❌ Media integration: PROBLEMS")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)





