#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This code has been has been written by Adam Coard, but was originally based 
# off of the Google Analytics 'Hello' tutorial API.  So, credit where it is due, 
# none of this is possible without Google's extensive API and documentation.


"""
Todo:

-Setup multiple account/site management (refactor 'get_first_profile_id')
-Build output system that renders utilizing HTML templates (Jinja)
-Have a discussion with Gary about what analytics/metrics he thinks are most important.
-Automatically calculate weekly date differences to query Google.
-Remove template rendering to a separate class after it's written (during early dev it's in AnalyticsWrapper)


Sample Usage:

  $ python analytics.py

  Currently this uses pdb.set_trace() to boot up the interpreter right after 
  results have been returned to `results`

"""

__author__ = 'arcoard@gmail.com (Adam Coard)'

import argparse
import sys
import pdb
import jinja2

from apiclient.errors import HttpError
from apiclient import sample_tools
from oauth2client.client import AccessTokenRefreshError

from datetime import date
from datetime import timedelta

class AnalyticsWrapper:
  """
  TODO: Expand so it can iterate over clients + add methods for different lookups.

  """

  def main(self, argv):
    # Authenticate and construct service.
    service, flags = sample_tools.init(
        argv, 'analytics', 'v3', __doc__, __file__,
        scope='https://www.googleapis.com/auth/analytics.readonly')

    # Try to make a request to the API. Print the results or handle errors.
    try:
      first_profile_id = self.get_first_profile_id(service)
      if not first_profile_id:
        print 'Could not find a valid profile for this user.'
      else:
        # results = get_top_keywords(service, first_profile_id)
        results = self.get_info_until_today(service, first_profile_id, 30)
        self.print_results(results)
        pdb.set_trace()

    except TypeError, error:
      # Handle errors in constructing a query.
      print ('There was an error in constructing your query : %s' % error)

    except HttpError, error:
      # Handle API errors.
      print ('Arg, there was an API error : %s : %s' %
             (error.resp.status, error._get_reason()))

    except AccessTokenRefreshError:
      # Handle Auth errors.
      print ('The credentials have been revoked or expired, please re-run '
             'the application to re-authorize')


  def get_first_profile_id(self, service):
    """Traverses Management API to return the first profile id.

    This first queries the Accounts collection to get the first account ID.
    This ID is used to query the Webproperties collection to retrieve the first
    webproperty ID. And both account and webproperty IDs are used to query the
    Profile collection to get the first profile id.

    Args:
      service: The service object built by the Google API Python client library.

    Returns:
      A string with the first profile ID. None if a user does not have any
      accounts, webproperties, or profiles.
    """

    accounts = service.management().accounts().list().execute()

    if accounts.get('items'):
      firstAccountId = accounts.get('items')[0].get('id')
      webproperties = service.management().webproperties().list(
          accountId=firstAccountId).execute()

      if webproperties.get('items'):
        firstWebpropertyId = webproperties.get('items')[0].get('id')
        profiles = service.management().profiles().list(
            accountId=firstAccountId,
            webPropertyId=firstWebpropertyId).execute()

        if profiles.get('items'):
          return profiles.get('items')[0].get('id')

    return None

  def get_top_keywords(self, service, profile_id):
    """Executes and returns data from the Core Reporting API.

    This queries the API for the top 25 organic search terms by visits.

    Args:
      service: The service object built by the Google API Python client library.
      profile_id: String The profile ID from which to retrieve analytics data.

    Returns:
      The response returned from the Core Reporting API.
    """

    return service.data().ga().get(
        ids='ga:' + profile_id,
        start_date='2014-04-01',
        end_date='2014-06-15',
        metrics='ga:visits',
        dimensions='ga:source,ga:keyword',
        sort='-ga:visits',
        filters='ga:medium==organic',
        start_index='1',
        max_results='25').execute()

  def get_info_until_today(self, service, profile_id, days):
    """
    TODO: Expand so that it does more than just look up sessions/sessionDuration for userType.
    """

    return service.data().ga().get(
      ids='ga:' + profile_id,
      start_date=self.days_from_today(days),
      end_date=self.days_from_today(0),
      dimensions='ga:userType',
      metrics='ga:sessions, ga:sessionDuration',
      start_index='1',
      max_results='25').execute()

  def days_from_today(self, days=0):
    """
    Returns the number of days in the past from today.  If input is omitted or at
    0, then it returns today.

    Args:
      days: Optional integer of number of days in the past you want the return date


    Returns:
      Isoformatted date, which can be fed directly into the start_date/end_date 
      params for the Google API.
    """
    today = date.today()
    if (days >= 0):
      days_delta = timedelta(days=days)
      days_in_past = today - days_delta
      return days_in_past.isoformat()
    elif (days < 0):
      print("Make sure the input is >= 0")
      return False

  def organize_results(self, results):
    """
    Returns the results in a dictionary (or list?)

    Make sure to return a new object which is sorted - do not sort the original results.

    Still in dev.
    """

    return False

  def print_results(self, results):
    """Prints out the results.

    This prints out the profile name, the column headers, and all the rows of
    data.

    Args:
      results: The response returned from the Core Reporting API.
    """

    print
    print 'Profile Name: %s' % results.get('profileInfo').get('profileName')
    print

    # Print header.
    output = []
    for header in results.get('columnHeaders'):
      output.append('%30s' % header.get('name'))
    print ''.join(output)

    # Print data table.
    if results.get('rows', []):
      for row in results.get('rows'):
        output = []
        for cell in row:
          output.append('%30s' % cell)
        print ''.join(output)

    else:
      print 'No Rows Found'


  #TODO:  The functions below are to be separated out into a separate class!  
  #Design without access to instance+class variables

  def render_template(self):
    '''
    Renders to HTML template. The input must be organized first through organize_results().

    Still in dev.
    '''
    templateLoader = jinja2.FileSystemLoader( searchpath="./" )
    templateEnv = jinja2.Environment( loader=templateLoader )
    TEMPLATE_FILE = "default.template"
    template = templateEnv.get_template( TEMPLATE_FILE )

    FAVORITES = [ "chocolates", "lunar eclipses", "rabbits" ]
    templateVars = { "title" : "Test Example",
                 "description" : "A simple inquiry of function.",
                 "favorites" : FAVORITES
               }

    outputText = template.render( templateVars )

    self.write_to_file(outputText, 'temp.html')
    
    return outputText

  def write_to_file(self, content, output_file_name):
    """
    In dev. 
    """
    try:
      output = open(output_file_name, 'w')
      output.write(content)
      output.close()
    except Error, e:
      print "Exception: " + e


if __name__ == '__main__':
  api = AnalyticsWrapper()
  api.main(sys.argv)