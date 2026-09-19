import zipfile
import os

# 1. نام فایل زیپ خود را اینجا بنویسید
ZIP_FILE_NAME = 'my_project.zip' 
# 2. نام فایل خروجی نهایی
OUTPUT_MD_FILE = 'project_code_combined.md'

def get_language_syntax(file_name):
    """تشخیص زبان برای خوانایی بهتر در هوش مصنوعی"""
    if file_name.endswith('.py'): return 'python'
    if file_name.endswith('.html'): return 'html'
    if file_name.endswith('.css'): return 'css'
    if file_name.endswith('.js'): return 'javascript'
    if file_name.endswith('.json'): return 'json'
    return ''

def zip_to_single_md(zip_path, output_path):
    with zipfile.ZipFile(zip_path, 'r') as archive:
        with open(output_path, 'w', encoding='utf-8') as md_file:
            md_file.write(f"# 📦 ساختار کدهای پروژه: {os.path.basename(zip_path)}\n")
            md_file.write(f"این فایل به صورت یکپارچه برای پردازش بهینه در هوش مصنوعی تولید شده است.\n\n---\n")
            
            for file_info in archive.infolist():
                if file_info.is_dir() or 'MACOSX' in file_info.filename or '.git' in file_info.filename:
                    continue
                
                file_name = file_info.filename
                
                # فقط فایل‌های متنی و کدی مجاز باشند
                allowed_extensions = ['.py', '.html', '.css', '.js', '.json', '.txt', '.md']
                if not any(file_name.lower().endswith(ext) for ext in allowed_extensions):
                    continue
                
                try:
                    with archive.open(file_info) as file:
                        content = file.read().decode('utf-8', errors='ignore')
                        lang = get_language_syntax(file_name)
                        
                        # نوشتن مسیر فایل به عنوان تیتر و قرار دادن کدها در بلوک مخصوص
                        md_file.write(f"\n\n## 📄 فایل: `{file_name}`\n")
                        md_file.write(f"```{lang}\n")
                        md_file.write(content)
                        md_file.write("\n```\n")
                        md_file.write("\n---")
                        print(f"✅ کد فایل ادغام شد: {file_name}")
                except Exception as e:
                    print(f"❌ خطا در خواندن فایل {file_name}: {e}")

    print(f"\n🎉 عالی شد! تمام کدهای شما در یک فایل متنی فشرده جمع شدند: {output_path}")

# اجرا
zip_to_single_md(ZIP_FILE_NAME, OUTPUT_MD_FILE)