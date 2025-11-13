"""TrafficJunky Creative Upload Module."""

import logging
import time
from pathlib import Path
from typing import Dict, Optional, List
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)


class TJUploader:
    """Handles creative file uploads to TrafficJunky."""
    
    def __init__(self, dry_run: bool = True, take_screenshots: bool = True):
        """
        Initialize uploader.
        
        Args:
            dry_run: If True, simulate but don't actually upload
            take_screenshots: If True, take screenshots at each step
        """
        self.dry_run = dry_run
        self.take_screenshots = take_screenshots
        self.screenshot_counter = 0
    
    def upload_creative_batch(
        self,
        page: Page,
        file_paths: List[Path],
        screenshot_dir: Optional[Path] = None,
        creative_type: str = ''
    ) -> Dict:
        """
        Upload multiple creative files at once to TrafficJunky.
        
        Args:
            page: Playwright page object
            file_paths: List of file paths to upload
            screenshot_dir: Directory to save screenshots
            creative_type: Type of creatives (for tab navigation)
            
        Returns:
            Dictionary with upload results
        """
        result = {
            'status': 'failed',
            'creative_ids': [],
            'file_names': [fp.name for fp in file_paths],
            'uploaded_count': 0,
            'error': None
        }
        
        if not file_paths:
            result['error'] = "No files provided"
            return result
        
        try:
            logger.info(f"Processing batch upload: {len(file_paths)} files")
            
            # Step 1: Navigate to Media Library
            if not self._navigate_to_creative_library(page):
                result['error'] = "Failed to navigate to Media Library"
                return result
            
            self._take_screenshot(page, f"01_media_library", screenshot_dir)
            
            # Step 1.5: Capture existing Creative IDs BEFORE upload (for duplicate detection)
            existing_ids = self._get_existing_creative_ids(page)
            logger.info(f"Found {len(existing_ids)} existing creatives on page before upload")
            
            # Step 2: Click Native tab if this is a native creative
            step = 2
            if 'native' in creative_type.lower():
                if not self._click_native_tab(page):
                    result['error'] = "Failed to click Native tab"
                    return result
                self._take_screenshot(page, f"02_native_tab_clicked", screenshot_dir)
                step = 3
                
                # Step 3: Click appropriate Native sub-tab
                if 'native_video' in creative_type.lower():
                    if not self._click_native_rollover_tab(page):
                        result['error'] = "Failed to click Rollover sub-tab"
                        return result
                    self._take_screenshot(page, f"03_rollover_tab_clicked", screenshot_dir)
                elif 'native_image' in creative_type.lower():
                    self._take_screenshot(page, f"03_static_banner_selected", screenshot_dir)
                step = 4
            
            # Step N: Click Upload button
            is_native = 'native' in creative_type.lower()
            if not self._click_add_creative(page, is_native=is_native):
                result['error'] = "Failed to click Upload button"
                return result
            
            self._take_screenshot(page, f"{step:02d}_upload_button_clicked", screenshot_dir)
            step += 1
            
            # Wait for upload panel/form to be ready
            logger.info("Waiting for upload form to be ready...")
            time.sleep(1)
            
            # Dry run check
            if self.dry_run:
                logger.info(f"DRY RUN: Would upload {len(file_paths)} files")
                self._take_screenshot(page, f"{step:02d}_DRY_RUN_ready", screenshot_dir)
                result['status'] = 'dry_run_success'
                return result
            
            # Step N: Upload multiple files directly to hidden input (skip Browse button)
            # This avoids opening the native macOS file dialog which Playwright can't control
            if not self._upload_files_batch(page, file_paths):
                result['error'] = "Failed to upload files"
                return result
            
            self._take_screenshot(page, f"{step:02d}_files_uploaded", screenshot_dir)
            step += 1
            
            # Wait for all files to finish processing
            logger.info(f"Waiting for {len(file_paths)} files to complete processing...")
            if not self._wait_for_upload_completion(page, len(file_paths), screenshot_dir, step):
                result['error'] = "Upload processing timeout"
                return result
            
            step += 1
            
            # Extract Creative IDs (multiple) - only NEW ones created during this upload
            uploaded_file_names = [fp.name for fp in file_paths]
            creative_ids = self._extract_new_creative_ids(page, uploaded_file_names, existing_ids)
            
            if creative_ids:
                logger.info(f"✓ Successfully uploaded {len(creative_ids)} NEW creatives")
                result['status'] = 'success'
                result['creative_ids'] = creative_ids
                result['uploaded_count'] = len(creative_ids)
                self._take_screenshot(page, f"{step:02d}_success_batch", screenshot_dir)
            else:
                logger.warning("⚠ No new Creative IDs found - files may already exist on TJ")
                result['error'] = "No new Creative IDs (possible duplicates)"
                result['status'] = 'duplicate'  # New status for duplicates
                self._take_screenshot(page, f"{step:02d}_WARNING_no_new_ids", screenshot_dir)
            
            return result
            
        except Exception as e:
            logger.error(f"✗ Batch upload failed: {e}")
            result['error'] = str(e)
            self._take_screenshot(page, f"ERROR_batch_upload", screenshot_dir)
            return result
    
    def upload_creative(
        self,
        page: Page,
        file_path: Path,
        screenshot_dir: Optional[Path] = None,
        creative_type: str = ''
    ) -> Dict:
        """
        Upload a single creative file to TrafficJunky.
        
        Args:
            page: Playwright page object
            file_path: Path to file to upload
            screenshot_dir: Directory to save screenshots
            
        Returns:
            Dictionary with upload results:
            {
                'status': 'success' | 'failed' | 'dry_run_success',
                'creative_id': str or None,
                'file_name': str,
                'error': str or None
            }
        """
        result = {
            'status': 'failed',
            'creative_id': None,
            'file_name': file_path.name,
            'error': None
        }
        
        try:
            logger.info(f"Processing creative upload: {file_path.name}")
            
            # Step 1: Navigate to Media Library
            if not self._navigate_to_creative_library(page):
                result['error'] = "Failed to navigate to Media Library"
                return result
            
            self._take_screenshot(page, f"01_media_library", screenshot_dir)
            
            # Step 2: Click Native tab if this is a native creative
            step = 2
            if 'native' in creative_type.lower():
                if not self._click_native_tab(page):
                    result['error'] = "Failed to click Native tab"
                    return result
                self._take_screenshot(page, f"02_native_tab_clicked", screenshot_dir)
                step = 3
                
                # Step 3: Click appropriate Native sub-tab
                # For images: Static Banner (default, already selected)
                # For videos: Click Rollover sub-tab
                if 'native_video' in creative_type.lower():
                    if not self._click_native_rollover_tab(page):
                        result['error'] = "Failed to click Rollover sub-tab"
                        return result
                    self._take_screenshot(page, f"03_rollover_tab_clicked", screenshot_dir)
                elif 'native_image' in creative_type.lower():
                    # Static Banner is default, just take screenshot to confirm
                    self._take_screenshot(page, f"03_static_banner_selected", screenshot_dir)
                step = 4
            
            # Step N: Click Add Creative/Upload button
            is_native = 'native' in creative_type.lower()
            if not self._click_add_creative(page, is_native=is_native):
                result['error'] = "Failed to click Add Creative button"
                return result
            
            self._take_screenshot(page, f"{step:02d}_upload_button_clicked", screenshot_dir)
            step += 1
            
            # Step N+1: Click "Browse your computer" to open file dialog
            if not self._click_browse_button(page):
                result['error'] = "Failed to click Browse your computer button"
                return result
            
            self._take_screenshot(page, f"{step:02d}_browse_clicked", screenshot_dir)
            step += 1
            
            # Wait for file upload dialog to appear
            logger.info("Waiting for file upload dialog...")
            time.sleep(1)
            
            # Verify file input is present
            try:
                page.wait_for_selector('input[type="file"]', state='attached', timeout=5000)
                logger.info("✓ File upload dialog appeared")
                self._take_screenshot(page, f"{step:02d}_upload_dialog_ready", screenshot_dir)
            except:
                logger.warning("Could not verify file upload dialog")
            
            # Dry run check - now we've verified the full flow works
            if self.dry_run:
                logger.info(f"DRY RUN: Would upload {file_path}")
                # Close the file dialog by pressing Escape or clicking Cancel
                try:
                    logger.info("Closing file dialog...")
                    page.keyboard.press('Escape')
                    time.sleep(0.5)
                    logger.info("✓ File dialog closed")
                except:
                    logger.debug("Could not close file dialog (may have closed automatically)")
                result['status'] = 'dry_run_success'
                return result
            
            # Step N: Upload file
            if not self._upload_file(page, file_path):
                result['error'] = "Failed to upload file"
                return result
            
            self._take_screenshot(page, f"{step:02d}_file_uploaded", screenshot_dir)
            step += 1
            
            # Step N+1: Wait for upload to process
            logger.info("Waiting for upload to process...")
            time.sleep(3)
            
            # Step N+2: Extract Creative ID
            creative_id = self._extract_creative_id(page)
            
            if creative_id:
                logger.info(f"✓ Successfully uploaded creative. ID: {creative_id}")
                result['status'] = 'success'
                result['creative_id'] = creative_id
                self._take_screenshot(page, f"{step:02d}_success_id_{creative_id}", screenshot_dir)
            else:
                logger.warning("Upload may have succeeded but could not extract Creative ID")
                result['error'] = "Could not extract Creative ID"
                self._take_screenshot(page, f"{step:02d}_ERROR_no_id", screenshot_dir)
            
            return result
            
        except Exception as e:
            logger.error(f"✗ Upload failed for {file_path.name}: {e}")
            result['error'] = str(e)
            self._take_screenshot(page, f"ERROR_{file_path.stem}", screenshot_dir)
            return result
    
    def _navigate_to_creative_library(self, page: Page) -> bool:
        """Navigate to TrafficJunky Media Library page."""
        try:
            url = "https://advertiser.trafficjunky.com/media-library"
            logger.info(f"Navigating to {url}")
            
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for page to load - look for media library indicators
            try:
                page.wait_for_selector('text=MEDIA LIBRARY', state='visible', timeout=5000)
            except:
                # Alternative: check for upload button or file input
                page.wait_for_selector('input[type="file"]', state='attached', timeout=5000)
            
            logger.info("✓ Media Library loaded")
            return True
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False
    
    def _click_native_tab(self, page: Page) -> bool:
        """Click the Native tab in Media Library."""
        try:
            logger.info("Clicking Native tab...")
            
            # Try multiple selectors for the Native tab
            selectors = [
                'a#native_tab',
                'a[href="#native"]',
                'a.tab:has-text("Native")',
                'text=Native'
            ]
            
            for selector in selectors:
                try:
                    tab = page.locator(selector).first
                    if tab.is_visible(timeout=2000):
                        logger.info(f"Found Native tab with selector: {selector}")
                        tab.click()
                        time.sleep(1)  # Wait for tab content to load
                        logger.info("✓ Native tab clicked")
                        return True
                except:
                    continue
            
            logger.error("Could not find Native tab")
            return False
            
        except Exception as e:
            logger.error(f"Failed to click Native tab: {e}")
            return False
    
    def _click_native_static_tab(self, page: Page) -> bool:
        """Click the Static Banner sub-tab within Native tab (for images)."""
        try:
            logger.info("Clicking Static Banner sub-tab...")
            
            # Try multiple selectors for the Static Banner radio/button
            selectors = [
                'label:has(input#native_static)',
                'input#native_static',
                'label.native_static',
                'label:has-text("Static Banner")',
                'input[name="native_type"][value="0"]'
            ]
            
            for selector in selectors:
                try:
                    element = page.locator(selector).first
                    if element.is_visible(timeout=2000):
                        logger.info(f"Found Static Banner tab with selector: {selector}")
                        element.click()
                        time.sleep(0.5)  # Wait for sub-tab content to load
                        logger.info("✓ Static Banner sub-tab clicked")
                        return True
                except:
                    continue
            
            logger.error("Could not find Static Banner sub-tab")
            return False
            
        except Exception as e:
            logger.error(f"Failed to click Static Banner sub-tab: {e}")
            return False
    
    def _click_native_rollover_tab(self, page: Page) -> bool:
        """Click the Rollover sub-tab within Native tab (for videos)."""
        try:
            logger.info("Clicking Rollover sub-tab...")
            
            # Try multiple selectors for the Rollover radio/button
            selectors = [
                'label:has(input#native_rollover)',
                'input#native_rollover',
                'label.native_rollover',
                'label:has-text("Rollover")',
                'input[name="native_type"][value="1"]'
            ]
            
            for selector in selectors:
                try:
                    element = page.locator(selector).first
                    if element.is_visible(timeout=2000):
                        logger.info(f"Found Rollover tab with selector: {selector}")
                        element.click()
                        time.sleep(0.5)  # Wait for sub-tab content to load
                        logger.info("✓ Rollover sub-tab clicked")
                        return True
                except:
                    continue
            
            logger.error("Could not find Rollover sub-tab")
            return False
            
        except Exception as e:
            logger.error(f"Failed to click Rollover sub-tab: {e}")
            return False
    
    def _click_add_creative(self, page: Page, is_native: bool = False) -> bool:
        """Click the 'Add Creative' or 'Upload' button."""
        try:
            logger.info("Looking for Add Creative button...")
            
            # Try multiple possible selectors for the upload button
            # For Native creatives, try the specific native upload button first
            if is_native:
                selectors = [
                    'button#newImage',
                    'button:has-text("Upload New Creatives")',
                    'button.greenButton',
                    '[data-gtm-index="uploadCreativesMediaLibrary"]',
                    'button:has-text("Add Creative")',
                    'button:has-text("Upload")'
                ]
            else:
                selectors = [
                    'button:has-text("Add Creative")',
                    'button:has-text("Upload Creative")',
                    'a:has-text("Add Creative")',
                    'button:has-text("Upload")',
                    '[data-action="add-creative"]',
                    '.btn:has-text("Add")'
                ]
            
            for selector in selectors:
                try:
                    button = page.locator(selector).first
                    if button.is_visible(timeout=2000):
                        logger.info(f"Found button with selector: {selector}")
                        button.click()
                        time.sleep(1)
                        logger.info("✓ Add Creative button clicked")
                        return True
                except:
                    continue
            
            logger.error("Could not find Add Creative button")
            return False
            
        except Exception as e:
            logger.error(f"Failed to click Add Creative: {e}")
            return False
    
    def _click_browse_button(self, page: Page) -> bool:
        """Click the 'Browse your computer' button to open file dialog."""
        try:
            logger.info("Looking for Browse your computer button...")
            
            # Try multiple possible selectors for the browse button
            selectors = [
                'span:has-text("Browse your computer")',
                'span.smallButton.greyButton:has-text("Browse")',
                'span.greyButton:has-text("Browse")',
                'button:has-text("Browse your computer")',
                '.smallButton:has-text("Browse")'
            ]
            
            for selector in selectors:
                try:
                    button = page.locator(selector).first
                    if button.is_visible(timeout=2000):
                        logger.info(f"Found Browse button with selector: {selector}")
                        button.click()
                        time.sleep(1)
                        logger.info("✓ Browse button clicked")
                        return True
                except:
                    continue
            
            logger.error("Could not find Browse your computer button")
            return False
            
        except Exception as e:
            logger.error(f"Failed to click Browse button: {e}")
            return False
    
    def _upload_file(self, page: Page, file_path: Path) -> bool:
        """Upload file via file input."""
        try:
            logger.info(f"Uploading file: {file_path}")
            
            # Look for file input element
            # Try multiple possible selectors
            selectors = [
                'input[type="file"]',
                'input[accept*="image"]',
                'input[accept*="video"]',
                '#creative-upload',
                '[name="creative"]'
            ]
            
            for selector in selectors:
                try:
                    file_input = page.locator(selector).first
                    if file_input.is_visible(timeout=2000):
                        logger.info(f"Found file input with selector: {selector}")
                        file_input.set_input_files(str(file_path))
                        logger.info("✓ File uploaded")
                        return True
                except:
                    continue
            
            # If file input not visible, it might be hidden - try all inputs
            logger.info("File input not visible, trying hidden inputs...")
            file_inputs = page.locator('input[type="file"]')
            count = file_inputs.count()
            
            if count > 0:
                file_inputs.first.set_input_files(str(file_path))
                logger.info("✓ File uploaded via hidden input")
                return True
            
            logger.error("Could not find file input element")
            return False
            
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            return False
    
    def _upload_files_batch(self, page: Page, file_paths: List[Path]) -> bool:
        """Upload multiple files at once via file input."""
        try:
            logger.info(f"Uploading batch: {len(file_paths)} files")
            
            # Look for file input element
            selectors = [
                'input[type="file"]',
                'input[accept*="image"]',
                'input[accept*="video"]',
                '#creative-upload',
                '[name="creative"]'
            ]
            
            for selector in selectors:
                try:
                    file_input = page.locator(selector).first
                    if file_input.is_visible(timeout=2000):
                        logger.info(f"Found file input with selector: {selector}")
                        # Set multiple files at once
                        file_paths_str = [str(fp) for fp in file_paths]
                        file_input.set_input_files(file_paths_str)
                        logger.info(f"✓ {len(file_paths)} files uploaded")
                        return True
                except:
                    continue
            
            # If file input not visible, it might be hidden - try all inputs
            logger.info("File input not visible, trying hidden inputs...")
            file_inputs = page.locator('input[type="file"]')
            count = file_inputs.count()
            
            if count > 0:
                file_paths_str = [str(fp) for fp in file_paths]
                file_inputs.first.set_input_files(file_paths_str)
                logger.info(f"✓ {len(file_paths)} files uploaded via hidden input")
                return True
            
            logger.error("Could not find file input element")
            return False
            
        except Exception as e:
            logger.error(f"Failed to upload batch: {e}")
            return False
    
    def _wait_for_upload_completion(self, page: Page, expected_count: int, screenshot_dir: Optional[Path], step: int) -> bool:
        """
        Wait for all uploaded files to finish processing on TrafficJunky.
        Monitors Dropzone states: dz-preview -> dz-processing -> dz-success dz-complete
        
        Args:
            page: Playwright page object
            expected_count: Number of files that were uploaded
            screenshot_dir: Directory for screenshots
            step: Current step number for screenshot naming
            
        Returns:
            True if all uploads completed, False if timeout
        """
        max_wait_time = expected_count * 30  # 30 seconds per file (more conservative)
        poll_interval = 2  # Check every 2 seconds
        elapsed = 0
        
        logger.info(f"Waiting for {expected_count} files to complete processing...")
        
        while elapsed < max_wait_time:
            try:
                # Step 1: Check if processing message is still visible
                processing_msg = page.locator('div.processingMessage.customMessage')
                if processing_msg.count() > 0 and processing_msg.is_visible():
                    logger.info(f"  [{elapsed}s] TrafficJunky processing uploads...")
                    time.sleep(poll_interval)
                    elapsed += poll_interval
                    continue
                
                # Step 2: Check Dropzone file states
                # Look for all file preview elements
                all_files = page.locator('div.dz-preview')
                total_files = all_files.count()
                
                if total_files == 0:
                    logger.info(f"  [{elapsed}s] Waiting for file previews to appear...")
                    time.sleep(poll_interval)
                    elapsed += poll_interval
                    continue
                
                # Check how many are complete (have both dz-success and dz-complete)
                completed_files = page.locator('div.dz-preview.dz-success.dz-complete')
                completed_count = completed_files.count()
                
                # Check how many are still processing
                processing_files = page.locator('div.dz-preview.dz-processing')
                processing_count = processing_files.count()
                
                logger.info(f"  [{elapsed}s] Status: {completed_count}/{expected_count} complete, {processing_count} processing")
                
                # All expected files are complete
                if completed_count >= expected_count:
                    logger.info(f"✓ All {expected_count} uploads completed successfully! (took {elapsed}s)")
                    self._take_screenshot(page, f"{step:02d}_all_uploads_complete", screenshot_dir)
                    logger.info("Waiting 5 seconds for extra safety buffer...")
                    time.sleep(5)  # Extra 5 seconds safety buffer
                    return True
                
                time.sleep(poll_interval)
                elapsed += poll_interval
                    
            except Exception as e:
                logger.debug(f"Error checking upload status: {e}")
                time.sleep(poll_interval)
                elapsed += poll_interval
        
        # Timeout - take screenshot and return false
        try:
            completed_files = page.locator('div.dz-preview.dz-success.dz-complete')
            completed_count = completed_files.count()
            logger.warning(f"⚠ Timeout waiting for uploads ({completed_count}/{expected_count} completed after {elapsed}s)")
        except:
            logger.warning(f"⚠ Timeout waiting for uploads after {elapsed}s")
        
        self._take_screenshot(page, f"{step:02d}_TIMEOUT_incomplete", screenshot_dir)
        return False
    
    def _extract_creative_id(self, page: Page) -> Optional[str]:
        """
        Extract Creative ID from page after upload.
        
        According to user: ID appears in <span class="bannerId">1032382001</span>
        
        Returns:
            Creative ID as string, or None if not found
        """
        try:
            logger.info("Extracting Creative ID...")
            
            # Wait for bannerId span to appear
            page.wait_for_selector('span.bannerId', state='visible', timeout=10000)
            
            # Get the text content
            banner_id_element = page.locator('span.bannerId').first
            creative_id = banner_id_element.text_content()
            
            if creative_id and creative_id.strip():
                creative_id = creative_id.strip()
                logger.info(f"✓ Extracted Creative ID: {creative_id}")
                return creative_id
            else:
                logger.warning("bannerId element found but no text content")
                return None
                
        except Exception as e:
            logger.warning(f"Could not extract Creative ID: {e}")
            
            # Try alternative methods
            try:
                # Look for any element containing a number that looks like a Creative ID
                logger.info("Trying alternative Creative ID extraction...")
                
                # Try to find in page content
                page_content = page.content()
                import re
                # Look for 10+ digit numbers (Creative IDs are typically long)
                matches = re.findall(r'\b\d{10,}\b', page_content)
                if matches:
                    # Return the first match (most likely the Creative ID)
                    logger.info(f"Found possible Creative ID via regex: {matches[0]}")
                    return matches[0]
                    
            except Exception as e2:
                logger.error(f"Alternative extraction also failed: {e2}")
            
            return None
    
    def _get_existing_creative_ids(self, page: Page) -> set:
        """
        Get all existing Creative IDs from ALL pages (handles pagination).
        This is used to detect which IDs are NEW after upload.
        
        IMPORTANT: TJ Media Library shows 12 creatives per page with pagination.
        We need to loop through ALL pages to capture every existing Creative ID,
        otherwise we might think IDs from page 2+ are "new" when they're not.
        
        Uses the data-id attribute from .creativeContainer elements:
        <div class="creativeContainer" data-id="1032530511">
        
        Returns:
            Set of existing Creative ID strings from ALL pages
        """
        try:
            logger.info("Collecting existing Creative IDs from all pages...")
            all_existing_ids = set()
            current_page = 1
            max_pages = 50  # Safety limit to prevent infinite loops
            
            while current_page <= max_pages:
                # Wait for page to be stable
                time.sleep(0.5)
                
                # Get all creative containers on current page
                containers = page.locator('div.creativeContainer[data-id]')
                count = containers.count()
                
                if count == 0 and current_page == 1:
                    # No creatives at all (empty library)
                    logger.info("Media Library is empty (no existing creatives)")
                    return set()
                
                # Collect IDs from current page
                page_ids = []
                for i in range(count):
                    try:
                        container = containers.nth(i)
                        creative_id = container.get_attribute('data-id')
                        if creative_id:
                            creative_id = creative_id.strip()
                            all_existing_ids.add(creative_id)
                            page_ids.append(creative_id)
                    except Exception as e:
                        logger.debug(f"Failed to get data-id at index {i}: {e}")
                
                logger.info(f"  Page {current_page}: Found {len(page_ids)} creatives")
                
                # Check if there's a "Next" button for pagination
                # Common pagination selectors in TJ interface
                next_button_selectors = [
                    'a.page-link:has-text("Next")',
                    'button:has-text("Next")',
                    'a[rel="next"]',
                    'li.next:not(.disabled) a',
                    'a.pagination-next',
                    '.pagination .next a'
                ]
                
                next_button = None
                for selector in next_button_selectors:
                    try:
                        btn = page.locator(selector).first
                        if btn.count() > 0 and btn.is_visible(timeout=1000):
                            # Check if button is not disabled
                            is_disabled = False
                            try:
                                parent = btn.locator('xpath=..').first
                                if parent.get_attribute('class') and 'disabled' in parent.get_attribute('class'):
                                    is_disabled = True
                            except:
                                pass
                            
                            if not is_disabled:
                                next_button = btn
                                break
                    except:
                        continue
                
                # If no next button found, we're on the last page
                if not next_button:
                    logger.info(f"  No more pages (reached page {current_page})")
                    break
                
                # Click next button to go to next page
                try:
                    logger.debug(f"  Clicking next page...")
                    next_button.click()
                    time.sleep(1)  # Wait for page to load
                    current_page += 1
                except Exception as e:
                    logger.debug(f"Could not click next button: {e}")
                    break
            
            logger.info(f"✓ Collected {len(all_existing_ids)} existing Creative IDs from {current_page} page(s)")
            return all_existing_ids
            
        except Exception as e:
            logger.warning(f"Error getting existing IDs (falling back to current page only): {e}")
            # Fallback: just get current page
            try:
                containers = page.locator('div.creativeContainer[data-id]')
                count = containers.count()
                existing_ids = set()
                for i in range(count):
                    try:
                        container = containers.nth(i)
                        creative_id = container.get_attribute('data-id')
                        if creative_id:
                            existing_ids.add(creative_id.strip())
                    except:
                        pass
                return existing_ids
            except:
                return set()
    
    def _extract_new_creative_ids(
        self, 
        page: Page, 
        uploaded_file_names: List[str], 
        existing_ids: set
    ) -> List[str]:
        """
        Extract only NEW Creative IDs that were created during this upload.
        
        Strategy:
        1. Get all current Creative IDs from .creativeContainer[data-id]
        2. Compare with existing_ids (captured before upload) to find NEW ids
        3. For each new ID, get its filename from .creativeName label
        4. Match filename with our uploaded_file_names list
        5. Return Creative IDs in the same order as uploaded_file_names
        
        Args:
            page: Playwright page object
            uploaded_file_names: List of filenames we just uploaded
            existing_ids: Set of Creative IDs that existed before upload
            
        Returns:
            List of NEW Creative ID strings, in same order as uploaded_file_names
        """
        try:
            logger.info(f"Extracting NEW Creative IDs (excluding {len(existing_ids)} existing)...")
            
            # Wait for creative containers to appear/update
            page.wait_for_selector('div.creativeContainer[data-id]', state='visible', timeout=15000)
            time.sleep(1)  # Extra buffer for DOM to stabilize
            
            # Get all creative containers
            containers = page.locator('div.creativeContainer[data-id]')
            count = containers.count()
            
            logger.info(f"Found {count} total creatives on page after upload")
            
            # Build map: filename -> Creative ID (only for NEW creatives)
            filename_to_id = {}
            new_ids_found = []
            
            for i in range(count):
                try:
                    container = containers.nth(i)
                    creative_id = container.get_attribute('data-id')
                    
                    if not creative_id:
                        continue
                    
                    creative_id = creative_id.strip()
                    
                    # Check if this is a NEW ID (not in existing_ids)
                    if creative_id in existing_ids:
                        logger.debug(f"  Skipping existing ID: {creative_id}")
                        continue
                    
                    # This is a new ID! Get its filename
                    # Look for .creativeName label within this container
                    name_label = container.locator('label.creativeName').first
                    if name_label.count() > 0:
                        filename = name_label.text_content()
                        if filename:
                            filename = filename.strip()
                            # Remove file extension for matching
                            filename_base = filename
                            
                            # Map this filename to Creative ID
                            filename_to_id[filename] = creative_id
                            new_ids_found.append(creative_id)
                            logger.info(f"  ✓ NEW Creative: {filename} -> ID: {creative_id}")
                    
                except Exception as e:
                    logger.warning(f"Failed to process container at index {i}: {e}")
            
            if not new_ids_found:
                logger.warning("⚠ No new Creative IDs found - all files may be duplicates")
                return []
            
            logger.info(f"Found {len(new_ids_found)} NEW Creative IDs")
            
            # Match uploaded files to Creative IDs (preserve order)
            matched_ids = []
            for uploaded_name in uploaded_file_names:
                # Try exact match first
                if uploaded_name in filename_to_id:
                    matched_ids.append(filename_to_id[uploaded_name])
                    logger.debug(f"  Matched: {uploaded_name} -> {filename_to_id[uploaded_name]}")
                else:
                    # Try without extension
                    name_no_ext = uploaded_name.rsplit('.', 1)[0]
                    if name_no_ext in filename_to_id:
                        matched_ids.append(filename_to_id[name_no_ext])
                        logger.debug(f"  Matched (no ext): {name_no_ext} -> {filename_to_id[name_no_ext]}")
                    else:
                        logger.warning(f"  ⚠ Could not match uploaded file: {uploaded_name}")
            
            if len(matched_ids) != len(uploaded_file_names):
                logger.warning(
                    f"Expected {len(uploaded_file_names)} matches but got {len(matched_ids)}. "
                    f"Some files may be duplicates or failed to upload."
                )
            
            return matched_ids
                
        except Exception as e:
            logger.error(f"Could not extract new Creative IDs: {e}")
            return []
    
    def _take_screenshot(self, page: Page, name: str, screenshot_dir: Optional[Path]):
        """Take a screenshot if enabled."""
        if not self.take_screenshots or not screenshot_dir:
            return
        
        try:
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            self.screenshot_counter += 1
            filename = f"{self.screenshot_counter:02d}_{name}.png"
            filepath = screenshot_dir / filename
            page.screenshot(path=str(filepath))
            logger.debug(f"Screenshot saved: {filename}")
        except Exception as e:
            logger.debug(f"Screenshot failed: {e}")

