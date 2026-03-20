import os
import re

base_dir = r"c:\Users\RISHITHA\Downloads\Resume_analyser-main (1)\Resume_analyser-main\frontend"
splash_path = os.path.join(base_dir, "public", "splash.html")
index_path = os.path.join(base_dir, "index.html")

with open(splash_path, 'r', encoding='utf-8') as f:
    splash_content = f.read()

# 1. Add Vite icon to head
splash_content = splash_content.replace(
    '<title>CareerDNA</title>',
    '<link rel="icon" type="image/svg+xml" href="/vite.svg" />\n  <title>CareerDNA</title>'
)

# 2. Add splash-active scope to body rules
splash_content = splash_content.replace(
    'body::before {',
    'body.splash-active::before {'
)

# Replace html, body with just html, body and move overflow to splash-active
splash_content = splash_content.replace(
    '''    html, body {
      width: 100%; height: 100%;
      background: var(--bg-deep);
      overflow: hidden;
      font-family: 'Inter', sans-serif;
    }''',
    '''    html, body {
      width: 100%; height: 100%;
      background: var(--bg-deep);
      font-family: 'Inter', sans-serif;
    }
    body.splash-active {
      overflow: hidden;
    }'''
)

# 3. Add class to body tag
splash_content = splash_content.replace('<body>', '<body class="splash-active">')

# 4. Update window.location.href line to hide splash / show React
splash_content = splash_content.replace(
    "window.location.href = '/';",
    """
          document.body.classList.remove('splash-active');
          document.querySelectorAll('.corner, #splash').forEach(el => el.style.display = 'none');
          document.getElementById('root').style.display = 'block';
          gsap.to(cover, { opacity: 0, duration: 0.5, onComplete: () => cover.style.display = 'none' });
    """
)

# 5. Append Vite Entry Scripts right before </body>
vite_entry = '''
  <div id="root" style="display: none;"></div>
  <script type="module" src="/src/main.jsx"></script>
'''
splash_content = splash_content.replace('</body>', vite_entry + '</body>')

with open(index_path, 'w', encoding='utf-8') as f:
    f.write(splash_content)

print("Successfully merged splash.html into index.html")
