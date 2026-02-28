import os
import json
import asyncio
import sys
import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# Fix for Windows asyncio event loop (Required for Playwright)
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

def extract_courses_from_json():
    # Automatically find the exact folder where this Python script is saved
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create the full, exact paths to the JSON files
    finance_path = os.path.join(script_dir, 'curriculum_data.json')
    cse_path = os.path.join(script_dir, 'cse_curriculum_data.json')
    
    print(f"📂 Looking for Finance JSON at: {finance_path}")
    print(f"📂 Looking for CSE JSON at: {cse_path}")
    
    all_courses = set()
    
    # 1. Read Business/Finance JSON
    try:
        with open(finance_path, 'r', encoding='utf-8') as f:
            finance_data = json.load(f)
            for category, classes in finance_data.get('curriculum', {}).items():
                for course in classes:
                    all_courses.add(course['id'])
        print("✅ Finance JSON loaded successfully.")
    except Exception as e:
        print(f"⚠️ Failed to read Finance JSON: {e}")

    # 2. Read CSE JSON
    try:
        with open(cse_path, 'r', encoding='utf-8') as f:
            cse_data = json.load(f)
            for category, classes in cse_data.get('curriculum', {}).items():
                for course in classes:
                    all_courses.add(course['id'])
        print("✅ CSE JSON loaded successfully.")
    except Exception as e:
        print(f"⚠️ Failed to read CSE JSON: {e}")

    # Format IDs (e.g., "CSE 2221" instead of "CSE2221" if they are mashed together)
    # We also sort them alphabetically so the console output looks organized
    target_list = sorted(list(all_courses))
    print(f"\n🎯 Successfully loaded {len(target_list)} unique courses to scrape.\n")
    return target_list, script_dir

async def scrape_osu_courses(target_courses):
    results = {course: [] for course in target_courses}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True) 
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        total = len(target_courses)
        for index, target_course in enumerate(target_courses, 1):
            
            # Hard reset for SPA (Single Page Application)
            await page.goto("about:blank") 
            
            url = f"https://classes.osu.edu/#/?q={target_course.replace(' ', '%20')}&client=class-search-ui&campus=col&p=1"
            print(f"[{index}/{total}] 🌐 Scraping: {target_course}")
            
            try:
                await page.goto(url, timeout=60000)
                
                try:
                    await page.wait_for_selector(f"text={target_course}", timeout=20000)
                except:
                    await page.wait_for_selector(".course, .search-results", timeout=15000)

                await asyncio.sleep(5) 

                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                course_block = None
                for div in soup.find_all('div', class_=re.compile(r'course|result-container')):
                    # Spaceless comparison to avoid hidden HTML space bugs
                    target_clean = target_course.replace(" ", "").lower()
                    div_clean = div.get_text().replace(" ", "").lower()
                    
                    if target_clean in div_clean:
                        course_block = div
                        break
                
                if course_block:
                    rows = course_block.select('.result-row') or course_block.find_all('div', recursive=True)
                    
                    for row in rows:
                        text = row.get_text(separator=" ")
                        
                        if "am" in text.lower() or "pm" in text.lower():
                            
                            # IDENTIFY COMPONENT TYPE
                            comp_type = "Lecture" 
                            if re.search(r'\b(Recitation|REC)\b', text, re.I):
                                comp_type = "Recitation"
                            elif re.search(r'\b(Laboratory|Lab|LAB)\b', text, re.I):
                                comp_type = "Lab"
                            elif re.search(r'\b(Seminar|SEM)\b', text, re.I):
                                comp_type = "Seminar"

                            # EXTRACT TIME
                            time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:am|pm)\s*-\s*\d{1,2}:\d{2}\s*(?:am|pm))', text, re.I)
                            time_str = time_match.group(1) if time_match else "TBA"

                            # EXTRACT DAYS (No duplicates)
                            active_days = []
                            for active_el in row.find_all(class_=re.compile(r'active')):
                                day_txt = active_el.get_text(strip=True)
                                if len(day_txt) <= 2 and day_txt not in active_days: 
                                    active_days.append(day_txt)
                            
                            days_val = "".join(active_days)
                            
                            # SAVE IF VALID
                            if time_str != "TBA" and days_val != "":
                                entry = {"type": comp_type, "days": days_val, "time": time_str}
                                if entry not in results[target_course]:
                                    results[target_course].append(entry)
                    
                    print(f"      ✅ Saved {len(results[target_course])} sections.")
                else:
                    print(f"      ❌ No sections found.")

            except Exception as e:
                print(f"      💥 Error: {e}")

        await browser.close()
    return results

async def main():
    # 1. Pull the list from the JSON files and get the save directory
    targets, script_dir = extract_courses_from_json()
    
    if not targets:
        print("❌ No courses found to scrape. Check your JSON files and paths.")
        return

    # 2. Scrape the list
    print("🚀 Starting bulk scrape. This will take several minutes...\n")
    data = await scrape_osu_courses(targets)
    
    # 3. Save the mega-dictionary in the exact same folder
    save_path = os.path.join(script_dir, 'full_course_schedule.json')
    with open(save_path, 'w') as f:
        json.dump(data, f, indent=4)
        
    print(f"\n🎉 DONE! All schedules saved to:\n{save_path}")

if __name__ == "__main__":
    asyncio.run(main())