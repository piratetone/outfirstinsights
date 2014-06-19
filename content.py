import jinja2

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from datetime import date

class ContentPresentor:
  """
  Takes the result from the AnalyticsWrapper.organize_results(), and readies 
  the data for presentation.  Output methods will include:

    1. Render via HTML template to create an HTML file.
    2. Email
  """

  def __init__(self, content, site_name):
    """
    Content must be a list of 
    """
    if isinstance(content, list):
      self.content = content  
    else:
      raise Exception("Error in instantiating ContentPresentor: Input must be a list.")

    self.site_name = site_name
    #Pretty site name = http://wwww.THISPARTHERE.com.
    if 'www' in site_name:
      self.pretty_site_name = site_name[len('http://www.'):-len('.com')]
    else:
      self.pretty_site_name = site_name[len('http://'):-len('.com')]


  def run(self):
    self.render_template(self.content, self.site_name)

  def render_template(self, content, site_name):
    '''
    Renders HTML template with data.
    '''
    template_data = content
    templateLoader = jinja2.FileSystemLoader( searchpath="./" )
    templateEnv = jinja2.Environment( loader=templateLoader )
    TEMPLATE_FILE = "default.template"
    template = templateEnv.get_template( TEMPLATE_FILE )
    templateVars = { "title" : "Outfirst Insights",
              "site_name": site_name,
              "tables" : template_data,
              'date' : date.today().isoformat()
           }

    outputText = template.render( templateVars )
    self.write_to_file(outputText, self.pretty_site_name + '.html')
    return outputText
    

  def email(self, rendered_template):
    """This function currently doesn't work because I don't have the SMTP info.
    """
    sending_email = "outfirst@email.com"
    recepient = "your@email.com"

    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Outfirst Insights" #TODO: 'for the week of XXX'
    msg['From'] = sending_email
    msg['To'] = recepient

    content = MIMEText(html, rendered_template)
    msg.attach(content)
    # Send the message via local SMTP server.
    s = smtplib.SMTP('localhost') #TODO: Fill this out.
    s.sendmail(sending_email, recipient, msg.as_string())
    s.quit()


  def write_to_file(self, content, output_file_name):
    """
    Simplifies creating/writing to files.  Used for template rendering but generic enough for other purposes.
    """
    try:
      output = open(output_file_name, 'w')
      output.write(content)
      output.close()
    except Error, e:
      print "Write to file exception: " + e