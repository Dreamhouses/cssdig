import os, re, urllib2, time, datetime, operator, sys, gzip, shutil
from urlparse import urlparse, urljoin, urlunparse
from collections import OrderedDict
from collections import Counter
from bs4 import BeautifulSoup
from cStringIO import StringIO

start_time = time.time()

# Build defaults.
build_dir = "report"
build_file = build_dir + "/index.html"
layout_tmpl = 'template/index.tmpl'

# Remove the build dir and make it again.
if os.path.isdir(build_dir):
    shutil.rmtree(build_dir)
os.makedirs(build_dir)

#Get URL and properties from PHP
url = sys.argv[1]

# Uncomment to debug
#url = "http://inkling.com/"

prop_on_arr = [
    "background",
    "border",
    "color",
    "content",
    "display",
    "font",
    "font-family",
    "font-size",
    "font-style",
    "font-weight",
    "height",
    "line-height",
    "width",
    "z-index"
];

# Domains that can't or shouldn't be included.
domain_blacklist = [
    'use.typekit.com',
    'fonts.googleapis.com',
    'cloud.webtype.com',
]

# Get timestamp.
ts = time.time()
timestamp = datetime.datetime.fromtimestamp(ts).strftime('%B %d, %Y at %H:%M:%S')

# Parse the url.
url_parsed = urlparse(url)

css_urls_all = []
css_urls_clean = []
css_urls_bad = []
css_combined = ""
checkbox_html = ""

def getRemoteURL(url):
    req = urllib2.Request(url, headers={'User-Agent' : "Magic Browser"})
    doc = urllib2.urlopen(req)
    if doc.info().get('Content-Encoding') == 'gzip':
        buf = StringIO(doc.read())
        f = gzip.GzipFile(fileobj=buf)
        return f.read()
    else:
        return doc.read()

soup = BeautifulSoup(getRemoteURL(url))

# Find all <link> elements.
for link in soup.find_all('link'):
    # Get the rel attr of the <link>.
    rel = link.get('rel')[0]
    if rel.lower() == 'stylesheet':

        # If it's a stylesheet, get the link to the css sheet.
        css_href_parsed = urlparse(link.get('href'))

        # Test for query string, include only if needed.
        query_string = ""
        if not css_href_parsed.query == "":
            query_string = "?" + css_href_parsed.query

        # Resolve the path to the CSS files.
        full_css_path = urlunparse((css_href_parsed.scheme or url_parsed.scheme, css_href_parsed.netloc or url_parsed.netloc, os.path.join(os.path.dirname(url_parsed.path), css_href_parsed.path + query_string), None, None, None))

        #Create list of CSS files on the page.
        css_urls_all.append(full_css_path)

# Go through all the css paths.
for u in css_urls_all:
    host = urlparse(u).hostname
    # Concatenate all CSS files into one long string if they are not blacklisted.
    if not host in domain_blacklist:
        try:
            req = urllib2.Request(u, headers={'User-Agent' : "Magic Browser"})
            doc = urllib2.urlopen(req)
            if doc.info().get('Content-Encoding') == 'gzip':
                buf = StringIO(doc.read())
                f = gzip.GzipFile(fileobj=buf)
                css_combined += f.read()
            else:
                css_combined += doc.read()
            css_urls_clean.append(u)
        except urllib2.HTTPError, e:
            css_urls_bad.append(u)

# Check for styles in head.
style_css = ''.join([s.get_text() for s in soup.find_all('style')])
if not style_css:
    css_combined = css_combined + style_css

# spaces may be safely collapsed as generated content will collapse them anyway
css_combined = re.sub(r'\s+', ' ', css_combined )

# add semicolon if needed
css_combined = re.sub(r'([a-zA-Z0-9"]\S)}', r'\g<1>'+';}', css_combined )
# new line after opening bracket
css_combined = re.sub(r'({)', r' '+'\g<1>'+'\n', css_combined )
# new line after semicolon
css_combined = re.sub(r'(;)', r'\g<1>'+'\n', css_combined )
# tab in plus one space in declarations so the highlighter js
# can distinguish between height and min-height
css_combined = re.sub(r'(.*;)', r'\t '+'\g<1>', css_combined )
# new line after closing bracket
css_combined = re.sub(r'(})', r'\g<1>'+'\n', css_combined )
# add space after colon if needed
css_combined = re.sub(r'(\t.*?):(\S)', r'\g<1>'+': '+'\g<2>', css_combined )


# Find all instances of !important.
important_values = re.findall("!important", css_combined)
report_html = "<table class='report-entry'>\n"
report_html += "<tr class='totals'>\n<td>!important</td>" + "<td>" + str(len(important_values)) + "</td>\n</tr>\n"
report_html += "</table>\n"

# # Find all instances of TODO.
# todo_values = re.findall("TODO", css_combined)
# report_html += "<table class='report-entry'>\n"
# report_html += "<tr class='totals'>\n<td>TODO</td>" + "<td>" + str(len(todo_values)) + "</td>\n</tr>\n"
# report_html += "</table>\n"

# Find all properties in the combined CSS.
prop_regex = "[{|;]\s*([a-zA-Z0-9-]*)\s*:"
properties = re.findall(prop_regex, css_combined)
properties = list(set(properties))
properties.sort()

# Run through all the properties.
for p in properties:
    regex = "(?<!-)"+p+"\s*:\s*(.*?)[;|}]"
    values = re.findall(regex, css_combined)
    values.sort()
    cnt = Counter(values)

    prop_checked = ""
    table_style_default ="style='display:none'"

    if p in prop_on_arr:
        prop_checked = "checked='checked' "
        table_style_default = ""

    checkbox_html += "<li><input type='checkbox' " + prop_checked + "id='checkbox-"+p+"' name='checkbox-"+p+"'><label for='checkbox-"+p+"'>" + p + "</label></li>\n"

    report_html += "<table class='report-entry' id='table-" + p + "' "+ table_style_default +">\n";
    report_html += "<tr class='totals'>\n<td>"+p+"</td>" + "<td>" + str(len(values)) + "</td>\n</tr>\n"

    for key, value in sorted(cnt.iteritems(), key=lambda (k,v): (k,v)):
        color_example = ""
        key = key.lstrip()
        if p == "color" or p == "background":
            report_html += "<tr>\n<td><div class='color-example-wrap'><span class='color-example' style='background:"+key+"'></span>" + p +": " + "%s;</div></td><td>%s</td>\n</tr>\n" % (key, value)
        else:
            report_html += "<tr>\n<td>" + p +": " + "%s;</td><td>%s</td>\n</tr>\n" % (key, value)
    report_html += "</table>\n"


# CSS found in <style> blocks.
style_css = ''.join([s.get_text() for s in soup.find_all('style')])

# HTML for parsed CSS files.
css_urls_list_good = ''.join(["<li><a href='"+u+"'>" + u + "</a></li>" for u in css_urls_clean])

# HTML for unreachable CSS files.
if css_urls_bad:
    css_urls_list_bad = ''.join(["<li><a href='"+b+"'>" + b + "</a></li>" for b in css_urls_bad])

# Time elapsed
time_elapsed = time.time() - start_time
time_elapsed = str(round(time_elapsed,1))

# Start collecting the HTML.
header_html = "<div class='stats'>\n"
header_html += "<h3>URL Dug</h3><p><a href='"+url+"'/>"+url+"</a></p>\n"
header_html += "<h3>CSS Dug</h3><ul>" + css_urls_list_good + "</ul>\n"
if css_urls_bad:
    header_html += "<h3>Skipped</h3><ul class='unparsed'>" + css_urls_list_bad + "</ul>\n"
header_html += "<h3>Dug</h3><p>"+timestamp+" taking "+time_elapsed+" seconds</p>\n"
header_html += "</div>\n"

layout_tmpl_html = open(layout_tmpl).read()
final_html_output = layout_tmpl_html\
    .replace("{{ checkbox_html }}", checkbox_html)\
    .replace("{{ css_combined }}", css_combined)\
    .replace("{{ report_html }}", header_html + report_html);

tf = open(build_file, 'a')
tf.write(final_html_output)
tf.close()

shutil.copytree('assets/', build_dir+"/assets/")