# Questions for TJ Creative Upload Integration

Please answer these questions so I can create an accurate implementation plan for integrating TJ creative library uploads into the video processor.

---

## 1. How do creatives get uploaded to TJ currently?

- a) Manually through the TJ web interface (default assumption) 
**Your Answer:**
- a) Manually through the TJ web interface (default assumption) 
---

## 2. What should happen after video processing completes?

- a) Automatically upload the video + thumbnail to TJ Media Library and get back creative IDs
- b) Just save the files locally and you'll upload manually later
- c) Upload to TJ and automatically create a CSV file ready to use with campaigns

**Your Answer:**

- a) save the files locally and Automatically upload the video + thumbnail to TJ Media Library and get back creative IDs
V2 - automatically create a CSV file ready to use with campaigns
---

## 3. For the TJ upload, what information do you need to provide?

- a) Just the video/image file

**Your Answer:**
- a) Just the video/image file
---

## 4. Which video processor should this integrate with?

- a) `video_processor.py` (640x360 output + PNG thumbnails)

**Your Answer:**
- a) `video_processor.py` (640x360 output + PNG thumbnails) - This is already the correct format.
---

## 5. Based on checking the TJ API documentation, there doesn't appear to be a direct API endpoint for uploading creative files. The API only allows fetching campaign stats and managing campaigns with existing creative IDs. This means we might need to:

- a) Use Playwright automation (like the existing TJ_tool) to upload creatives through the web interface


**Your Answer:**
- a) Use Playwright automation (like the existing TJ_tool) to upload creatives through the web interface
---

## 6. What information should be included when uploading a creative?

For each video/image uploaded to TJ, what metadata should we include?
- Creative name (e.g., based on filename?)
- Tags/categories?
- Other fields?

**Your Answer:**

None you just upload the video and image.
---

## 7. What output format do you want after upload?

After successfully uploading creatives to TJ, should the tool:
- a) Just log the creative IDs to console
- b) Save creative IDs to a CSV/text file
- c) Automatically create a Native campaign CSV with the new creative IDs
- d) Other (please describe)

**Your Answer:**
- b) Save creative IDs to a CSV file ready to be used in the /Users/joshb/Desktop/Dev/Native_converter/Example_Code/TJ_tool propgram via native main

---

## Additional Notes

Please add any other requirements, preferences, or context that would be helpful:

**Your Notes:**

