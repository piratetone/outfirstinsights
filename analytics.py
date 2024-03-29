#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This code has been has been written by Adam Coard, but none of this is 
# possible without Google's extensive API and documentation.


"""
Todo:

->Extend functionality to link site to email address.
-->Note: The email returned by the Google API is for the account (i.e. all are arcoard@gmail.com)
-->How does Gary link email to client?  DB or file.py that is list of tuples with (email, websiteUrl)

--Have Gary create an Outfirst Insights account for Google Analytics.
  This account would be the 'record' of who is subscribed to Outfirst Insights.
  If someone unsubscribed, they'd be removed from the account.  This means all
  profiles in the account would be traversed and emailed too (see problems with email above)
  This would only require one client_secrets.json file!

Weekly Messages / Backend, How to Handle:
->Cron job on Python script is the simplest solution (<3hrs) (original idea)
->Requires manual unsubscription.

Build a Backend (database + website to interact with it.  User authentication, etc) (~10-15hrs)
-->Ability to unsubscribe
-->Send out weekly emails.
-->Added functionality: allows ways for clients to modify what analytics they get.

Sample Usage:

  $ python analytics.py

  Currently this uses pdb.set_trace() to boot up the interpreter right after 
  the template has been rendered.  API return == `results`

"""

__author__ = 'arcoard@gmail.com (Adam Coard)' #If you have any questions, shoot me an email!

import argparse
import sys
from content import ContentPresentor

from apiclient.errors import HttpError
from apiclient import sample_tools
from oauth2client.client import AccessTokenRefreshError

from datetime import date
from datetime import timedelta

debug = False
import pdb #For dev only.  Can remove for prod.

class AnalyticsWrapper:
  """This class is responsible for quering the Google Analytics API and organizing the responses.

  """

  def main(self, argv):
    # Authenticate and construct service.
    service, flags = sample_tools.init(
        argv, 'analytics', 'v3', __doc__, __file__,
        scope='https://www.googleapis.com/auth/analytics.readonly')

    # Try to make a request to the API. Print the results or handle errors.
    try:
      all_profile_ids = self.get_all_profile_ids(service)
      if not all_profile_ids:
        print 'Could not find a valid profile for this user.'
      else:
        for site in all_profile_ids:
          site_name = site[1]
          profile_id = site[0]
          combined_results = self.get_all_profile_analytics(service, profile_id)
          content = ContentPresentor(combined_results, site_name)
          content.run()
          if debug:
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

  def get_info_until_today(self, service, profile_id, days, metrics='ga:sessions,ga:pageviews', dimensions='', sort=''):
    """
    This is the core method which is used to make calls to the Google Analytics API.
    It is rarely used directly, instead intermediate wrapper functions like 
    get_weekly_pageviews() are called.

    It returns the unmodified API response, which can then be processed by organize_results().
    """

    if (sort):
      return service.data().ga().get(
        ids='ga:' + profile_id,
        start_date=self.days_from_today(days),
        end_date=self.days_from_today(0),
        dimensions=dimensions,
        sort=sort,
        metrics=metrics,
        start_index='1',
        max_results='25').execute()
    else:
      return service.data().ga().get(
        ids='ga:' + profile_id,
        start_date=self.days_from_today(days),
        end_date=self.days_from_today(0),
        dimensions=dimensions,
        metrics=metrics,
        start_index='1',
        max_results='25').execute()

  def get_top_keywords(self, service, profile_id):
    """Executes and returns data from the Core Reporting API.

    This queries the API for the top 25 organic search terms by visits.

    Args:
      service: The service object built by the Google API Python client library.
      profile_id: String The profile ID from which to retrieve analytics data.

    Returns:
      The response returned from the Core Reporting API.
    """
    # self.get_info_until_today(service, profile_id, 7, metrics='ga:visits', dimensions='ga:source,ga:keyword')
    output = service.data().ga().get(
        ids='ga:' + profile_id,
        start_date='2014-04-01',
        end_date='2014-06-15',
        metrics='ga:visits',
        dimensions='ga:source,ga:keyword',
        sort='-ga:visits',
        filters='ga:medium==organic',
        start_index='1',
        max_results='25').execute()
    output['description'] = "Shows the top 25 organic search terms by visits."
    return output

  def get_sources(self, service, profile_id):
    output = self.get_info_until_today(service, profile_id, 365, 
      metrics='ga:sessions,ga:pageviews,ga:sessionDuration',
      dimensions='ga:source',
      sort='-ga:sessions')
    output['description'] = 'Referalls to the site from all websites, sorted by sessions.'
    return output

  def get_social_sources(self, service, profile_id):
    output = self.get_info_until_today(service, profile_id, 365, 
      metrics='ga:sessions,ga:pageviews,ga:sessionDuration',
      dimensions='ga:socialNetwork',
      sort='-ga:sessions')
    output['description'] = 'Referalls to site from social networks, sorted by sessions.'

    #Remove the non-social/'other' row from the list.
    for row in output['rows']:
      if row[0] == '(not set)':
        output['rows'].remove(row)

    return output
        
  def get_weekly_pageviews(self, service, profile_id):
    output = self.get_info_until_today(service, profile_id, 7, metrics='ga:sessions,ga:pageviews')
    output['description'] = 'Pageviews for the last 7 days.'
    return output

  def get_yearly_pageviews(self, service, profile_id):
    output = self.get_info_until_today(service, profile_id, 365, metrics='ga:sessions,ga:pageviews')
    output['description'] = 'Pageviews for the last 365 days.'
    return output

  def get_top_pages(self, service, profile_id):
    output = self.get_info_until_today(service, profile_id, 365, 
      metrics='ga:pageviews,ga:uniquePageviews,ga:timeOnPage,ga:bounces,ga:entrances,ga:exits',
      dimensions='ga:pagePath',
      sort='-ga:entrances')
    output['description'] = 'Pages sorted by pageviews.'
    return output    

  def get_sessions(self, service, profile_id):
    output = self.get_info_until_today(service, profile_id, 365, metrics='ga:sessions')
    output['description'] = 'All sessions for the last 365 days.'
    return output

  def get_unique_sessions(self, service, profile_id):
    output = self.get_info_until_today(service, profile_id, 365, metrics='ga:users')
    output['description'] = 'Amount of unique visitors over the last 365 days.'
    return output    

  def get_leads(self, service, profile_id):
    """
    TODO: Verify that the query is the right way to get lead info.  'All' vs. numbering them explicitly.
    """
    output = self.get_info_until_today(service, profile_id, 365, 
      metrics="ga:goalStartsAll,ga:goalCompletionsAll,ga:goalValueAll",
      sort="-ga:goalCompletionsAll")
    output["description"] = "Overview of leads for the last 365 days."
    return output

  def get_lead_conversion_rate(self, service, profile_id):
    output = self.get_info_until_today(service, profile_id, 365, 
      metrics="ga:goalConversionRateAll")
    output['description'] = "The percentage of sessions which resulted in a conversion to at least one of your leads."
    return output

  def new_versus_returning(self, service, profile_id):
    output = self.get_info_until_today(service, profile_id, 365, dimensions='ga:userType', metrics='ga:sessions')
    output['description'] = 'New versus returning viewers over the last 365 days.'
    return output

  def get_location(self, service, profile_id):
    output = self.get_info_until_today(service, profile_id, 365, 
      dimensions='ga:country',)
    output['description'] = 'Pages sorted by pageviews.'
    return output   

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

  def get_all_profile_ids(self, service):
    """Traverses Management API to returns a list of tuples.  
    Tuple[0] is the profile id, tuple[1] is site URL
    """

    accounts = service.management().accounts().list().execute()
    account_ids = []
    web_property_responses = []
    web_property_ids = []
    profiles = []
    profile_ids = []

    if accounts.get('items'):
      for account in accounts.get('items'):
        account_ids.append(account.get('id'))
        account_id_response = service.management().webproperties().list(
          accountId=account.get('id')).execute()
        web_property_responses.append(account_id_response)

    
    if web_property_responses:
      index = 0 #Used to query the separate list, account_ids, so that each account_id and webPropertyId match up.
      for response in web_property_responses:
        for web_property in response.get('items'):
          web_property_id = web_property.get('id')
          profile_response = service.management().profiles().list(
            accountId=account_ids[index],
            webPropertyId=web_property_id).execute()
          if profile_response.get('items'): #Make sure profile_response is a full site and not an acct remnant
            profiles.append(profile_response)
            profile_ids.append( (profile_response.get('items')[0].get('id'), 
              profile_response.get('items')[0].get('websiteUrl') ))
        index += 1
      return profile_ids      

    return None

  def get_all_profile_analytics(self, service, profile_id):
    """Function that combines all the separate queries for account analytics into one call.
    This substantially cleans up the main() fn. 

    If you want to edit the order of the tables in the template, this is the function to edit.
    The tables will appear in the order that the functions are called within the .append() method.
    """
    combined_results = []
    combined_results.append([
      self.organize_results(self.get_social_sources(service, profile_id)),
      self.organize_results(self.get_sources(service, profile_id)),
      self.organize_results(self.get_weekly_pageviews(service, profile_id)),
      self.organize_results(self.get_yearly_pageviews(service, profile_id)),
      self.organize_results(self.get_top_pages(service, profile_id)),
      self.organize_results(self.get_leads(service, profile_id)),
      self.organize_results(self.get_lead_conversion_rate(service, profile_id)),
      self.organize_results(self.new_versus_returning(service, profile_id)),
      self.organize_results(self.get_location(service, profile_id)),
      self.organize_results(self.get_top_keywords(service, profile_id))
      ])
    
    return combined_results[0]


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

    OR: Manually inject a description into the return of each function, describing what
    the query looks up.
    e.g. "get_yearly_pageviews()" adds: output['description'] = 'Pageviews for the last 365 days'
    """
    output = {}
    output['headers'] = []
    output['rows'] = []
    output['totals'] = []
    output['description'] = results['description']

    try:
      for item in results['columnHeaders']:
        #Clean up the headers, remove the technical descriptions Google Analytics includes.
        header = item['name'].replace('ga:', '').capitalize()

        if header == 'Socialnetwork':
          header = 'Social network'
        if header == 'Sessionduration':
          header = 'Session duration (seconds)'
        if header == 'Pageviews':
          header = 'Page views'
        if header == 'Uniquepageviews':
          header = 'Unique page views'
        if header == 'Timeonpage':
          header = 'Time on page'
        if header == 'Pagepath':
          header = 'Page path'
        if header == 'Goalconversionrateall':
          header = 'Goal conversion rate (all goals)'
        if header == 'Goalstartsall':
          header = 'Goal starts (all)'
        if header == 'Goalcompletionsall':
          header = 'Goal completions (all)'
        if header == 'Goalvalueall':
          header ='Goal value (all)'

        output['headers'].append(header)

      for row in results['rows']:
        output['rows'].append(row)
      return output

    except Exception as e:
      print type(e)
      print e

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
  

if __name__ == '__main__':
  api = AnalyticsWrapper()
  api.main(sys.argv)
