#
# NOTE: the version 2.2 API is NOT in production yet, use the v2.1 library in the default branch. We are making this branch available
# for beta testers, but it is not ready for production use yet.
#
# NOTE to .NET developers, it is best if you edit this file in a Python aware IDE. Komodo IDE is a good choice. .NET tends to break
# indentation in Python fields, which will cause bugs.
#
# Python client library for v2.1/v2.2 Insightly API
# Brian McConnell <brian@insight.ly>
#

import base64
import json
import string
import urllib
import urllib2

class Insightly():
    """
    Insightly Python library for Insightly API v2.2
    Brian McConnell <brian@insight.ly>
   
    This library provides user friendly access to the version 2.2 REST API for Insightly. The library provides several services, including:
   
    * HTTPS request generation
    * Data type validation
    * Required field validation
   
    The library is built using Python standard libraries (no third party tools required, so it will run out of the box on most Python
    environments, including Google App Engine). The wrapper functions return native Python objects, typically dictionaries, or lists of
    dictionaries, so working with them is easily done using built in functions.
    
    The version 2.2 API adds several new endpoints which make it easy to make incremental changes to existing Insightly objects, such
    as to add a phone number to a contact, and also more closely mirrors the functionality available in the web app (such as the
    ability to follow and unfollow objects.s)
   
    USAGE:
   
    Simply include insightly.py in your project file, then do the following for to run a test suite:
   
    from insightly import Insightly
    i = Insightly(apikey='your API key', version='2.2')
    users = i.test()
   
    This will run an automatic test suite against your Insightly account. If the methods you need all pass, you're good to go!
   
    If you are working with very large recordsets, you should use ODATA filters to access data in smaller chunks. This is a good idea in
    general to minimize server response times.
   
    BASIC USE PATTERNS:
   
    CREATE/UPDATE ACTIONS
   
    These methods expect a dictionary containing valid data fields for the object. They will return a dictionary containing the object
    as stored on the server (if successful) or raise an exception if the create/update request fails. You indicate whether you want to
    create a new item by setting the record id to 0 or omitting it.
   
    To obtain sample objects, you can do the following:
   
    contact = i.addContact('sample')
    event = i.addEvent('sample')
    organization = i.addOrganization('sample')
    project = i.addProject('sample')
   
    This will return a random item from your account, so you can see what fields are required, along with representative field values.
   
    SEARCH ACTIONS
   
    These methods return a list of dictionaries containing the matching items. For example to request a list of all contacts, you call:
    i = Insightly(apikey='your API key')
    contacts = i.getContacts()
   
    SEARCH ACTIONS USING ODATA
   
    Search methods recognize top, skip, orderby and filters parameters, which you can use to page, order and filter recordsets.
   
    contacts = i.getContacts(top=200) # returns the top 200 contacts
    contacts = i.getContacts(orderby='FIRST_NAME desc', top=200) # returns the top 200 contacts, with first name descending order
    contacts = i.getContacts(top=200, skip=200) # return 200 records, after skipping the first 200 records
    contacts = i.getContacts(filters=['FIRST_NAME=\'Brian\''])    # get contacts where FIRST_NAME='Brian'
   
    IMPORTANT NOTE: when using OData filters, be sure to include escaped quotes around the search term, otherwise you will get a
    400 (bad request) error
   
    These methods will raise an exception if the lookup fails, or return a list of dictionaries if successful, or an empty list if no
    records were found.
   
    READ ACTIONS (SINGLE ITEM)
   
    These methods will return a single dictionary containing the requested item's details.
    e.g. contact = i.getContact(123456)
   
    DELETE ACTIONS
   
    These methods will return True if successful, or raise an exception.
    e.g. success = i.deleteContact(123456)
   
    IMAGE AND FILE ATTACHMENT MANAGEMENT
   
    The API calls to manage images and file attachments have not yet been implemented in the Python library. However you can access
    these directly via our REST API
   
    ISSUES TO BE AWARE OF
   
    This library makes it easy to integrate with Insightly, and by automating HTTPS requests for you, eliminates the most common causes
    of user issues. That said, the service is picky about rejecting requests that do not have required fields, or have invalid field values
    (such as an invalid USER_ID). When this happens, you'll get a 400 (bad request) error. Your best bet at this point is to consult the
    API documentation and look at the required request data.
   
    Write/update methods also have a dummy feature that returns sample objects that you can use as a starting point. For example, to
    obtain a sample task object, just call:
   
    task = i.addTask('sample')
   
    This will return one of the tasks from your Insightly account, so you can get a sense of the fields and values used.
   
    If you are working with large recordsets, we strongly recommend that you use ODATA functions, such as top and skip to page through
    recordsets rather than trying to fetch entire recordsets in one go. This both improves client/server communication, but also minimizes
    memory requirements on your end.
    
    TROUBLESHOOTING TIPS
    
    One of the main issues API users run into during write/update operations is a 400 error (bad request) due to missing required fields.
    If you are unclear about what the server is expecting, a good way to troubleshoot this is to do the following:
    
    * Using the web interface, create the object in question (contact, project, team, etc), and add sample data and child elements to it
    * Use the corresponding getNNNN() method to retrieve this object via the web API
    * Inspect the object's contents and structure
    
    Read operations via the API are generally quite straightforward, so if you get struck on a write operation, this is a good workaround,
    as you are probably just missing a required field or using an invalid element ID when referring to something such as a link to a contact.
    """
    def __init__(self, apikey='', version='2.1'):
	"""
	Instantiates the class, logs in, and fetches the current list of users. Also identifies the account owner's user ID, which
	is a required field for some actions. This is stored in the property Insightly.owner_id

	Raises an exception if login or call to getUsers() fails, most likely due to an invalid or missing API key
	"""
        if len(apikey) < 1:
            try:
                f = open('apikey.txt', 'r')
                apikey = f.read()
                print 'API Key read from disk as ' + apikey
            except:
                pass
        version = str(version)
        if version == '2.2' or version == '2.1':
            self.alt_header = 'Basic '
            self.apikey = apikey
            self.tests_run = 0
            self.tests_passed = 0
            if version == '2.1':
                self.baseurl = 'https://api.insightlydev.com/v' + version
                self.users = self.getUsers()
                self.version = version
                print 'CONNECTED: found ' + str(len(self.users)) + ' users'
                for u in self.users:
                    if u.get('ACCOUNT_OWNER', False):
                        self.owner_email = u.get('EMAIL_ADDRESS','')
                        self.owner_id = u.get('USER_ID', None)
                        self.owner_name = u.get('FIRST_NAME','') + ' ' + u.get('LAST_NAME','')
                        print 'The account owner is ' + self.owner_name + ' [' + str(self.owner_id) + '] at ' + self.owner_email
                        break
            else:
                self.baseurl = 'https://api.insightlydev.com/v' + version
                self.version = version
                print 'ASSUME connection proceeded, not all endpoints are implemented yet'
                self.owner_email = ''
                self.owner_id = 0
                self.owner_name = ''
        else:
            raise Exception('Python library only supports v2.1 or v2.2 APIs')
                
    def getMethods(self):
        """
        Returns a list of the callable methods in this library.
        """
        methods = [method for method in dir(self) if callable(getattr(self, method))]
        return methods
    
    def test(self, top=None):
        """
        This helper function runs a test suite against the API to verify the API and client side methods are working normally.
        This may not reveal all corner cases, but will do a basic sanity check against the system.
        
        USAGE:
        
        i = Insightly()
        i.test(top=500)         # run test suite, limit search methods to return first 500 records
        i.test(top=None)        # run test suite, with no limit on number of records returned by search functions   
        """
        
        print "Testing API ....."
        
        print "Testing authentication"
        
        passed = 0
        failed = 0
        
        #
        # call methods in self test mode
        #
        if self.version == '2.1':
            users = self.getUsers(test = True)                              # get users
            user_id = users[0]['USER_ID']                                   # get the user ID for the first user on the instance
            accounts = self.getAccount(test = True)                         # get account/instance information
            # comments = self.getComments(test = True)                      # get comments
            contact = self.getContacts(orderby = 'DATE_UPDATED_UTC desc', top = top, test = True)   # get test contact
            if contact is not None:
                contact_id = contact['CONTACT_ID']                      
                emails = self.getContactEmails(contact_id, test = True)     # get emails attached to contact
                notes = self.getContactNotes(contact_id, test = True)       # get notes attached to contact
                tasks = self.getContactTasks(contact_id, test = True)       # get tasks attached to contact
            contact = dict(
                SALUTATION = 'Mr',
                FIRST_NAME = 'Testy',
                LAST_NAME = 'McTesterson',
            )
            contact = self.addContact(contact, test=True)                   # test adding, updating and deleting a contact       
            countries = self.getCountries(test = True)                      # get countries
            currencies = self.getCurrencies(test = True)                    # get currencies
            custom_fields = self.getCustomFields(test = True)                # get custom fields
            if len(custom_fields) > 0:
                custom_field = custom_fields[0]
                custom_field = self.getCustomField(custom_field['CUSTOM_FIELD_ID'], test = True)
            emails = self.getEmails(top=top, test = True)                   # get emails
            if len(emails) > 0:
                email = emails[0]
                comment = self.addCommentToEmail(email['EMAIL_ID'], 'This is a test', user_id, test = True)
                self.deleteComment(comment['COMMENT_ID'], test = True)
            events = self.getEvents(top=top, test = True)                   # get events
            if len(events) > 0:
                event = events[0]
                event = self.getEvent(event['EVENT_ID'], test = True)
            event = dict(
                TITLE = 'Test Event',
                LOCATION = 'Somewhere',
                DETAILS = 'Details',
                START_DATE_UTC = '2014-07-12 12:00:00',
                END_DATE_UTC = '2014-07-12 13:00:00',
                OWNER_USER_ID = user_id,
                ALL_DAY = False,
                PUBLICLY_VISIBLE = True,
            )
            event = self.addEvent(event, test = True)                       # add event
            if event is not None:
                self.deleteEvent(event['EVENT_ID'], test = True)            # delete event
            categories = self.getFileCategories(test = True)                # get file categories
            category = dict(
                CATEGORY_NAME = 'Test Category',
                ACTIVE = True,
                BACKGROUND_COLOR = '000000',
            )
            category = self.addFileCategory(category, test = True)          # add file category
            if category is not None:
                self.deleteFileCategory(category['CATEGORY_ID'])            # delete file category
                
            #
            # TODO: add Leads related endpoints
            #
                
            notes = self.getNotes(test = True)                              # get notes
            if notes is not None:
                note = notes[0]
                note = self.getNote(note['NOTE_ID'], test = True)
                comments = self.getNoteComments(note['NOTE_ID'], test = True)
    
            categories = self.getOpportunityCategories(test = True)         # get opportunity categories
            category = dict(
                CATEGORY_NAME = 'Test Category',
                ACTIVE = True,
                BACKGROUND_COLOR = '000000',
            )
            category = self.addOpportunityCategory(category, test = True)   # add opportunity category
            self.deleteOpportunityCategory(category['CATEGORY_ID'], test = True)
            
            opportunities = self.getOpportunities(orderby='DATE_UPDATED_UTC desc', top=top, test = True)        # get opportunities
            if opportunities is not None:
                opportunity = opportunities[0]
                emails = self.getOpportunityEmails(opportunity['OPPORTUNITY_ID'], test = True)
                notes = self.getOpportunityNotes(opportunity['OPPORTUNITY_ID'], test = True)
                tasks = self.getOpportunityTasks(opportunity['OPPORTUNITY_ID'], test = True)
                history = self.getOpportunityStateHistory(opportunity['OPPORTUNITY_ID'], test = True)
                #
                # TODO: add v2.2 endpoints, test CRUD operations on child objects
                #
            
            opportunity = dict(
                OPPORTUNITY_NAME = 'This is a test',
                OPPORTUNITY_DETAILS = 'This is a test test test',
                OPPORTUNITY_STATE = 'OPEN',
            )
            
            opportunity = self.addOpportunity(opportunity, test = True)
            self.deleteOpportunity(opportunity['OPPORTUNITY_ID'], test = True)
            
            reasons = self.getOpportunityStateReasons(test = True)
            
            organizations = self.getOrganizations(top=top, orderby='DATE_UPDATED_UTC desc', test = True)
            if organizations is not None:
                organization = organizations[0]
                if organization is not None:
                    emails = self.getOrganizationEmails(organization['ORGANISATION_ID'], test = True)
                    notes = self.getOrganizationNotes(organization['ORGANISATION_ID'], test = True)
                    tasks = self.getOrganizationTasks(organization['ORGANISATION_ID'], test = True)
                    
            organization = dict(
                ORGANISATION_NAME = 'Foo Corp',
                BACKGROUND = 'Details',
            )
            organization = self.addOrganization(organization, test = True)
            self.deleteOrganization(organization['ORGANIZATION_ID'], test = True)
                
            pipelines = self.getPipelines(test = True)
            pipeline = self.getPipeline(pipelines[0]['PIPELINE_ID'], test = True)
            stages = self.getPipelineStages(test = True)
            stage = self.getPipelineStage(stages[0]['STAGE_ID'], test = True)
            
            projects = self.getProjects(top=top, orderby='DATE_UPDATED_UTC desc', test = True)
            if projects is not None:
                project = projects[0]
                project_id = project['PROJECT_ID']
                emails = self.getProjectEmails(project_id, test = True)
                notes = self.getProjectNotes(project_id, test = True)
                tasks = self.getProjectTasks(project_id, test = True)
                #
                # TODO: add v2.2 endpoints, test CRUD operations on child objects
                #
                
            categories = self.getProjectCategories(test = True)                     # get project categories
            category = dict(
                CATEGORY_NAME = 'Test Category',
                ACTIVE = True,
                BACKGROUND_COLOR = '000000',
            )
            category = self.addProjectCategory(category, test = True)               # add project category
            self.deleteProjectCategory(category['CATEGORY_ID'], test = True)        # delete project category
            
            relationships = self.getRelationships(test = True)                      # get relationships
            
            tasks = self.getTasks(top=top, orderby='DUE_DATE desc', test = True)    # get tasks
            
            teams = self.getTeams(test = True)                                      # get teams
            if teams is not None:
                team = teams[0]
                team_members = self.getTeamMembers(team['TEAM_ID'], test = True)    # get team members
                
            print str(self.tests_passed) + ' out of ' + str(self.tests_run) + ' tests passed'
            
        elif self.version == '2.2':
            #
            # Building out the v2.2 test suite. Only a few endpoints are live at the moment
            #
            # TODO: auto-fetch a contact via getContacts(), not implemented in v2.2 yet
            #
            contact_id = 104101695
            addresses = self.getContactAddresses(contact_id, test=True) # get contact addresses
            address = dict(
                ADDRESS_TYPE = 'Work',
                STREET = '101 Main St',
                CITY = 'Monaco',
                COUNTRY = 'Monaco',
            )
            address = self.addContactAddress(contact_id, address, test = True)
            if address is not None:
                self.deleteContactAddress(contact_id, address['ADDRESS_ID'], test = True)
            contactinfos = self.getContactContactInfos(contact_id, test=True)
            contactinfo = dict(
                TYPE = 'Phone',
                LABEL = 'Work',
                DETAIL = '+14155551234',
            )
            contactinfo = self.addContactContactInfo(contact_id, contactinfo, test = True)
            if contactinfo is not None:
                self.deleteContactContactInfo(contact_id, contactinfo['CONTACT_INFO_ID'], test = True)
            # events = self.getContactEvents(contact_id, test=True)       # get events linked to contact
            tags = self.getContactTags(contact_id, test=True)           # grt tags linked to contact
            tag = self.addContactTag(contact_id, 'foo', test=True)
            self.deleteContactTag(contact_id, 'foo', test=True)
            notes = self.getNotes(test = True)
            if len(notes) > 0:
                note = notes[0]
                note = self.addNote(note, test = True)
                note = dict(
                    TITLE = 'Test',
                    BODY = 'This is a test',
                    LINK_SUBJECT_ID = contact_id,
                    LINK_SUBJECT_TYPE = 'CONTACT',
                )
                note = self.addNote(note, test = True)
                if note is not None:
                    note_id = note.get('NOTE_ID',None)
                    if note_id is not None:
                        self.deleteNote(note_id, test=True)
        else:
            print 'Automated test suites only available for versions 2.1 and 2.2'
        
    def dictToList(self, data):
        """
        This helper function checks to see if the returned data is a list or a lone dict, string, int or float.
        If it is a lone item, it is appended to a list.
        
        Use case: a function may return a list of dictionaries, or a single dictionary, or a nullset. This function
        standardizes this to a list of dictionaries, or in the case of a null set, an empty list.
        """
        if type(data) is list:
            return data
        elif type(data) is dict or type(data) is str or type(data) is int or type(data) is float:
            l = list()
            l.append(data)
            return l
        elif data is None:
            return list()
        else:
            return list()
	
    def findUser(self, email):
	"""
	Client side function to quickly look up Insightly users by email. Returns a dictionary containing
	user details or None if not found. This is useful when you need to find the user ID for someone but
	only know their email addresses, for example when creating and assigning a new project or task. 
	"""
	for u in self.users:
	    if u.get('EMAIL_ADDRESS','') == email:
		return u
	    
    def generateRequest(self, url, method, data, alt_auth=None):
        """
        This method is used by other helper functions to generate HTTPS requests and parse
        server responses. This will minimize the amount of work developers need to do to
        integrate with the Insightly API, and will also eliminate common sources of errors
        such as authentication issues and malformed requests. Uses the urllib2 standard
        library, so it is not dependent on third party libraries like Requests
        """
        if type(url) is not str: raise Exception('url must be a string')
        if type(method) is not str: raise Exception('method must be a string')
        valid_method = False
        response = None
        text = ''
        if method == 'GET' or method == 'PUT' or method == 'DELETE' or method == 'POST':
            valid_method = True
        else:
            raise Exception('parameter method must be GET|DELETE|PUT|UPDATE')
        # generate full URL from base url and relative url
        full_url = self.baseurl + url
        if self.version == '2.2':
            print 'URL: ' + full_url
        request = urllib2.Request(full_url)
        if alt_auth is not None:
            request.add_header("Authorization", self.alt_header)
        else:
            base64string = base64.encodestring('%s:%s' % (self.apikey, '')).replace('\n', '')
            request.add_header("Authorization", "Basic %s" % base64string)   
        request.get_method = lambda: method
        request.add_header('Content-Type', 'application/json')
        # open the URL, if an error code is returned it should raise an exception
        if method == 'PUT' or method == 'POST':
            result = urllib2.urlopen(request, data)
        else:
            result = urllib2.urlopen(request)
        text = result.read()
        return text    
        
    def ODataQuery(self, querystring, top=None, skip=None, orderby=None, filters=None):
        """
        This helper function generates an OData compatible query string. It is used by many
        of the search functions to enable users to filter, page and order recordsets.
        """
        #
        # TODO: double check that this has been implemented correctly
        #
        if type(querystring) is str:
            if top is not None:
                if querystring == '':
                    querystring += '?$top=' + str(top)
                else:
                    querystring += '&$top=' + str(top)
            if skip is not None:
                if querystring == '':
                    querystring += '?$skip=' + str(skip)
                else:
                    querystring += '&$skip=' + str(skip)
            if orderby is not None:
                if querystring == '':
                    querystring += '?$orderby=' + urllib.quote(orderby)
                else:
                    querystring += '&$orderby=' + urllib.quote(orderby)
            if type(filters) is list:
                for f in filters:
                    f = string.replace(f,' ','%20')
                    f = string.replace(f,'=','%20eq%20')
                    f = string.replace(f,'>','%20gt%20')
                    f = string.replace(f,'<','%20lt%20')
                    if querystring == '':
                        querystring += '?$filter=' + f
                    else:
                        querystring += '&$filter=' + f
            return querystring
        else:
            return ''
        
    def getAccount(self, email=None, test=False):
        """
        Find which account is associated with the current API key, this endpoint will most likely be renamed to Instance
        """
        if test:
            try:
                text = self.generateRequest('/Accounts', 'GET', '')
                accounts = json.loads(text)
                print 'PASS: getAccount() : Found ' + str(len(accounts)) + ' linked to this instance'
                self.tests_run += 1
                self.tests_passed += 1
            except:
                print 'FAIL: getAccount()'
                self.tests_run += 1
        else:
            if email is not None:
                text = self.generateRequest('/Accounts?email=' + email, 'GET','', alt_auth=self.alt_header)
            else:
                text = self.generateRequest('/Accounts', 'GET', '')
            return json.loads(text)
    
    def deleteComment(self, id, test = False):
        """
        Delete a comment, expects the comment's ID (unique record locator).
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Comments/' + str(id), 'DELETE','')
                print 'PASS: deleteComment()'
                self.tests_passed += 1
                return True
            except:
                print 'FAIL: deleteComment()'
        else:
            text = self.generateRequest('/Comments/' + str(id), 'DELETE','')
            return True

    def getComments(self, id, test = False):
        """
        Gets comments for an object. Expects the parent object ID.
        """
        #
        # HTTP GET api.insight.ly/v2.2/Comments
        #
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Comments/' + str(id), 'GET', '')
                comments = json.loads(text)
                self.tests_passed += 1
                print 'PASS: getComments() found ' + str(len(comments)) + ' comments'
            except:
                print 'FAIL: getComments()'
        else:
            text = self.generateRequest('/Comments/' + str(id), 'GET', '')
            return json.loads(text)
    
    def updateComment(self, body, owner_user_id, comment_id=None, test = False):
        """
        Creates or updates a comment. If you are updating an existing comment, be sure to include the comment_id
        """
        if len(body) < 1:
            raise Exception('Comment body cannot be empty')
            return
        if type(owner_user_id) is not int:
            raise Exception('owner_user_id must be an integer, and must be a valid user id')
        data = dict(
            BODY = body,
            OWNER_USER_ID = owner_user_id,
        )
        if comment_id is not None and type(comment_id) is int:
            data['COMMENT_ID'] = comment_id
            
        if test:
            self.tests_run += 1
            try:
                urldata = urllib.urlencode(data)
                text = self.generateRequest('/Comments', 'PUT', urldata)
                comment = json.loads(text)
                self.tests_passed += 1
                print 'PASS: updateComment()'
                return comment
            except:
                print 'FAIL: updateComment()'
        else:
            urldata = urllib.urlencode(data)
            text = self.generateRequest('/Comments', 'PUT', urldata)
            return json.loads(text)
    
    def addContact(self, contact, test = False):
        """
        Add/update a contact on Insightly. The parameter contact should be a dictionary containing valid data fields
        for a contact, or the string 'sample' to request a sample object. When submitting a new contact, set the
        CONTACT_ID field to 0 or omit it.
        """
        if test:
            self.tests_run += 1
            try:
                contact = self.addContact(contact)
                print "PASS: addContact()"
                self.tests_passed += 1
                self.tests_run += 1
                try:
                    contact = self.addContact(contact)
                    print 'PASS: addContact(), update existing contact'
                    self.tests_passed += 1
                except:
                    print 'FAIL: addContact(), update existing contact'
                self.tests_run += 1
                try:
                    self.deleteContact(contact['CONTACT_ID'])
                    print 'PASS: deleteContact()'
                    self.tests_passed += 1
                except:
                    print 'FAIL: deleteContact()'
            except:
                contact = None
                print "FAIL: addContact()"
        else:
            if type(contact) is str:
                if contact == 'sample':
                    contacts = self.getContacts(top=1)
                    return contacts[0]
                else:
                    raise Exception('contact must be a dictionary with valid contact data fields, or the string \'sample\' to request a sample object')
            else:
                if type(contact) is dict:
                    if contact.get('CONTACT_ID', 0) > 0:
                        text = self.generateRequest('/Contacts', 'PUT', json.dumps(contact))
                    else:
                        text = self.generateRequest('/Contacts', 'POST', json.dumps(contact))
                    return json.loads(text)
                else:
                    raise Exception('contact must be a dictionary with valid contact data fields, or the string \'sample\' to request a sample object')
            
    def addContactAddress(self, contact_id, address, test = False):
        """
        Add/update an address linked to a contact in Insightly.
        """
        if self.version != '2.2':
            raise Exception('method only supported for version 2.2 API')
        if type(address) is dict:
            # validate data
            at = string.lower(address.get('ADDRESS_TYPE',''))
            if at == 'work' or at == 'home' or at == 'postal' or at == 'other':
                if test:
                    self.tests_run += 1
                    try:
                        address_id = address.get('ADDRESS_ID', None)
                        if address_id is not None:
                            text = self.generateRequest('/Contacts/' + str(contact_id) + '/Addresses', 'PUT', json.dumps(address))
                        else:
                            text = self.generateRequest('/Contacts/' + str(contact_id) + '/Addresses', 'POST',json.dumps(address))
                        address = json.loads(text)
                        self.tests_passed += 1
                        print 'PASS: addContactAddress()'
                        return address
                    except:
                        print 'FAIL: addContactAddress()'
                else:
                    address_id = address.get('ADDRESS_ID', None)
                    if address_id is not None:
                        text = self.generateRequest('/Contacts/' + str(contact_id) + '/Addresses', 'PUT', json.dumps(address))
                    else:
                        text = self.generateRequest('/Contacts/' + str(contact_id) + '/Addresses', 'POST',json.dumps(address))
                    return json.loads(text)
            else:
                raise Exception('TYPE must be home, work, postal or other')
        else:
            raise Exception('address must be a dictionary')
    
    def addContactContactInfo(self, contact_id, contactinfo, test = False):
        """
        Add/update a contact info linked to a contact
        """
        if self.version != '2.2':
            raise Exception('method only supported for v2.2 API')
        if type(contactinfo) is dict:
            # validate data
            ct = string.lower(contactinfo.get('TYPE',''))
            if ct == 'phone' or ct == 'email' or ct == 'pager' or ct == 'fax' or ct == 'website' or ct == 'other':
                if test:
                    self.tests_run += 1
                    try:
                        contact_info_id = contactinfo.get('CONTACT_INFO_ID', None)
                        if contact_info_id is not None:
                            text = self.generateRequest('/Contacts/' + str(contact_id) + '/ContactInfos', 'PUT', json.dumps(contactinfo))
                        else:
                            text = self.generateRequest('/Contacts/' + str(contact_id) + '/ContactInfos', 'POST', json.dumps(contactinfo))
                        contact_info = json.loads(text)
                        print 'PASS: addContactContactInfo()'
                        self.tests_passed += 1
                        return contact_info
                    except:
                        print 'FAIL: addContactContactInfo()'
                else:
                    contact_info_id = contactinfo.get('CONTACT_INFO_ID', None)
                    if contact_info_id is not None:
                        text = self.generateRequest('/Contacts/' + str(contact_id) + '/ContactInfos', 'PUT', json.dumps(contactinfo))
                    else:
                        text = self.generateRequest('/Contacts/' + str(contact_id) + '/ContactInfos', 'POST', json.dumps(contactinfo))
                    return json.loads(text)
            else:
                raise Exception('TYPE must be phone, email, pager, fax, website or other')
        else:
            raise Exception('contactinfo must be a dictionary')
        
    def addContactEvent(self, contact_id, event, test = False):
        """
        Add an event to a contact
        """
        if self.version != '2.2':
            raise Exception('method only supported for version 2.2 API')
        if type(event) is dict:
            if test:
                self.tests_run += 1
                try:
                    event_id = event.get('EVENT_ID', None)
                    if event_id is not None:
                        text = self.generateRequest('/Contacts/' + str(contact_id) + '/Events', 'PUT', json.dumps(event))
                    else:
                        text = self.generateRequest('/Contacts/' + str(contact_id) + '/Events', 'POST', json.dumps(event))
                    event = json.loads(text)
                    print 'PASS: addContactEvent()'
                    self.tests_passed += 1
                    return event
                except:
                    print 'FAIL: addContactEvent()'
            else:
                event_id = event.get('EVENT_ID', None)
                if event_id is not None:
                    text = self.generateRequest('/Contacts/' + str(contact_id) + '/Events', 'PUT', json.dumps(event))
                else:
                    text = self.generateRequest('/Contacts/' + str(contact_id) + '/Events', 'POST', json.dumps(event))
                event = json.loads(text)
                return event
        else:
            raise Exception('event must be a dictionary')
        
    def addContactFileAttachment(self, contact_id, file_attachment, test = False):
        """
        Add/update a file attachment for a contact
        """
        if self.version != '2.2':
            raise Exception('method only supported for version 2.2 API')
        if type(file_attachment) is dict:
            if test:
                self.tests_run += 1
                try:
                    file_attachment_id = file_attachment.get('FILE_ATTACHMENT_ID', None)
                    if file_attachment_id is not None:
                        text = self.generateRequest('/Contacts/' + str(contact_id) + '/FileAttachments', 'PUT', json.dumps(file_attachment))
                    else:
                        text = self.generateRequest('/Contacts/' + str(contact_id) + '/FileAttachments', 'POST', json.dumps(file_attachment))
                    file_attachment = json.loads(text)
                    print 'PASS: addContactFileAttachment()'
                    self.tests_passed += 1
                    return file_attachment
                except:
                    print 'FAIL: addContactFileAttachment()'
            else:
                file_attachment_id = file_attachment.get('FILE_ATTACHMENT_ID', None)
                if file_attachment_id is not None:
                    text = self.generateRequest('/Contacts/' + str(contact_id) + '/FileAttachments', 'PUT', json.dumps(file_attachment))
                else:
                    text = self.generateRequest('/Contacts/' + str(contact_id) + '/FileAttachments', 'POST', json.dumps(file_attachment))
                file_attachment = json.loads(text)
                return file_attachment
        else:
            raise Exception('file_attachment must be a dictionary')
        
    def addContactFollow(self, contact_id, test = False):
        """
        Start following a contact
        """
        if self.version != '2.2':
            raise Exception('method only supported for version 2.2 API')
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Contacts/' + str(contact_id) + '/Follow', 'POST', '')
                print 'PASS: addContactFollow()'
                self.tests_passed += 1
                return True
            except:
                print 'FAIL: addContactFollow()'
        else:
            text = self.generateRequest('/Contacts/' + str(contact_id) + '/Follow', 'POST', '')
            return True
    
    def addContactNote(self, contact_id, note, test = False):
        """
        Add/update a file attachment for a contact
        """
        if self.version != '2.2':
            raise Exception('method only supported for version 2.2 API')
        if type(note) is dict:
            if test:
                self.tests_run += 1
                try:
                    note_id = note.get('NOTE_ID', None)
                    if note_id is not None:
                        text = self.generateRequest('/Contacts/' + str(contact_id) + '/Notes', 'PUT', json.dumps(note))
                    else:
                        text = self.generateRequest('/Contacts/' + str(contact_id) + '/Notes', 'POST', json.dumps(note))
                    note = json.loads(text)
                    print 'PASS: addContactNote()'
                    self.tests_passed += 1
                    return note
                except:
                    print 'FAIL: addContactNote()'
            else:
                note_id = note.get('NOTE_ID', None)
                if note_id is not None:
                    text = self.generateRequest('/Contacts/' + str(contact_id) + '/Notes', 'PUT', json.dumps(note))
                else:
                    text = self.generateRequest('/Contacts/' + str(contact_id) + '/Notes', 'POST', json.dumps(note))
                note = json.loads(text)
                return note
        else:
            raise Exception('file_attachment must be a dictionary')
    
    
    def addContactTag(self, contact_id, tag, test = False):
        """
        Delete a tag(s) from a contact
        """
        if self.version != '2.2':
            raise Exception('method only supported for version 2.2 API')
        t = dict(TAG_NAME=tag)
        if test:
            self.tests_run += 1
            text = self.generateRequest('/Contacts/' + str(contact_id) + '/Tags', 'POST', json.dumps(t))
            tags = json.loads(text)
            print 'PASS: addContactTags()'
            self.tests_passed += 1
            return tags
            #except:
            #    print 'FAIL: addContactTags()'
        else:
            text = self.generateRequest('/Contacts/' + str(contact_id) + '/Tags', 'POST', json.dumps(t))
            return json.loads(text)
        
    def deleteContact(self, contact_id, test = False):
        """
        Deletes a comment, identified by its record id
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Contacts/' + str(contact_id), 'DELETE', '')
                print 'PASS: deleteContact()'
                self.tests_passed += 1
                return True
            except:
                print 'FAIL: deleteContact()'
        else:
            text = self.generateRequest('/Contacts/' + str(contact_id), 'DELETE', '')
            return True
    
    def deleteContactAddress(self, contact_id, address_id, test = False):
        """
        Delete an address linked to a contact in Insightly.
        """
        if self.version != '2.2':
            raise Exception('method only supported for version 2.2 API')
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Contacts/' + str(contact_id) + '/Addresses/' + str(address_id), 'DELETE', '')
                print 'PASS: deleteContactAddress()'
                self.tests_passed += 1
                return True
            except:
                print 'FAIL: deleteContactAddress()'
        else:
            text = self.generateRequest('/Contacts/' + str(contact_id) + '/Addresses/' + str(address_id), 'DELETE', '')
            return True
    
    def deleteContactContactInfo(self, contact_id, contact_info_id, test = False):
        """
        Delete a contact info from a contact
        """
        if self.version != '2.2':
            raise Exception('method only supported for version 2.2 API')
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Contacts/' + str(contact_id) + '/ContactInfos/' + str(contact_info_id), 'DELETE', '')
                print 'PASS: deleteContactContactInfo()'
                self.tests_passed += 1
                return True
            except:
                print 'FAIL: deleteContactContactInfo()'
        else:
            text = self.generateRequest('/Contacts/' + str(contact_id) + '/ContactInfos/' + str(contact_info_id), 'DELETE', '')
            return True
    
    def deleteContactEvent(self, contact_id, event_id, test = False):
        """
        Delete an event from a contact
        """
        if self.version != '2.2':
            raise Exception('method only supported for version 2.2 API')
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Contacts/' + str(contact_id) + '/Events/' + str(event_id), 'DELETE', '')
                print 'PASS: deleteContactEvent()'
                self.tests_passed += 1
                return True
            except:
                print 'FAIL: deleteContactEvent()'
        else:
            text = self.generateRequest('/Contacts/' + str(contact_id) + '/Events/' + str(event_id), 'DELETE', '')
            return True
        
    def deleteContactFileAttachment(self, contact_id, file_attachment_id, test = False):
        """
        Delete a file attachment from a contact
        """
        if self.version != '2.2':
            raise Exception('method only supported for version 2.2 API')
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Contacts/' + str(contact_id) + '/FileAttachments/' + str(file_attachment_id), 'DELETE', '')
                print 'PASS: deleteContactFileAttachment()'
                self.tests_passed += 1
                return True
            except:
                print 'FAIL: deleteContactFileAttachment()'
        else:
            text = self.generateRequest('/Contacts/' + str(contact_id) + '/FileAttachments/' + str(file_attachment_id), 'DELETE', '')
            return True
    
    def deleteContactFollow(self, contact_id, test = False):
        """
        Stop following a contact
        """
        if self.version != '2.2':
            raise Exception('method only supported for version 2.2 API')
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Contacts/' + str(contact_id) + '/Follow', 'DELETE','')
                print 'PASS: deleteContactFollow()'
                self.tests_passed += 1
                return True
            except:
                print 'FAIL: deleteContactFollow()'
        else:
            text = self.generateRequest('/Contacts/' + str(contact_id) + '/Follow', 'DELETE','')
            return True
        
    def deleteContactNote(self, contact_id, note_id, test=False):
        """
        Delete a note from a contact
        """
        if self.version != '2.2':
            raise Exception('method only supported for version 2.2 API')
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Contacts/' + str(contact_id) + '/Notes/' + str(note_id), 'DELETE', '')
                print 'PASS: deleteContactNote()'
                self.tests_passed += 1
                return True
            except:
                print 'FAIL: deleteContactNote()'
        else:
            text = self.generateRequest('/Contacts/' + str(contact_id) + '/Notes/' + str(note_id), 'DELETE', '')
            return True
        
    def deleteContactTag(self, contact_id, tag, test = False):
        """
        Delete a tag from a contact
        """
        if self.version != '2.2':
            raise Exception('method only supported for version 2.2 API')
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Contacts/' + str(contact_id) + '/Tags/' + tag, 'DELETE', '')
                print 'PASS: deleteContactTag()'
                self.tests_passed += 1
                return True
            except:
                print 'FAIL: deleteContactTag()'
        else:
            text = self.generateRequest('/Contacts/' + str(contact_id) + '/Tags/' + tag, 'DELETE', '')
            return True
    
    def getContacts(self, ids=None, email=None, tag=None, filters=None, top=None, skip=None, orderby=None, test = False):
        """
        Get a list of matching contacts, expects the following optional parameters:
        
        ids = list of contact IDs
        email = user's email address
        tag = tag or keyword
        
        In addition, this method also supports OData operators:
        
        top = return only the first N records in the recordset
        skip = skip the first N records in the recordset
        orderby = e.g. 'LAST_NAME desc'
        filters = a list of filter statements
        
        Example:
        
        i = Insightly()
        contacts = i.getContacts(top=200,filters=['FIRST_NAME=\'Brian\''])
        
        It returns a list of dictionaries or raises an exception in the case of a malformed server response
        """
        if ids is not None and type(ids) is not list:
            raise Exception('parameter ids must be a list')
        if email is not None and type(email) is not str:
            raise Exception('parameter email must be a string')
        if tag is not None and type(tag) is not str:
            raise Exception('parameter tag must be a string')
        if filters is not None and type(filters) is not list:
            raise Exception('parameter filters must be a list')
        querystring = self.ODataQuery('', top=top, skip=skip, orderby=orderby, filters=filters)
        if email is not None:
            querystring += '?email=' + email
        if tag is not None:
            if querystring == '':
                querystring += '?tag=' + tag
            else:
                querystring += '&tag=' + tag
        if ids is not None and len(ids) > 0:
            if querystring == '':
                querystring += '?ids='
            else:
                querystring += '&ids='
            for i in ids:
                querystring += i + ','
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Contacts' + querystring, 'GET', '')
                contact = self.dictToList(json.loads(text))[0]
                print 'PASS: getContacts()'
                self.tests_passed += 1
                return contact
            except:
                print 'FAIL: getContacts()'
                return
        else:
            text = self.generateRequest('/Contacts' + querystring, 'GET', '')
            return self.dictToList(json.loads(text))
    
    def getContact(self, contact_id, test = False):
        """
        Gets a specific contact, identified by its record id
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Contacts/' + str(contact_id), 'GET','')
                contact = json.loads(text)
                print 'PASS: getContact()'
                self.tests_passed += 1
            except:
                print 'FAIL: getContact()'
        else:
            text = self.generateRequest('/Contacts/' + str(contact_id), 'GET','')
            return json.loads(text)

    def getContactAddresses(self, contact_id, test = False):
        """
        Get addresses linked to a contact
        """
        if self.version != '2.2':
            raise Exception('method only supported for version 2.2 API')
        if test:
            self.tests_run += 1
            try:            
                text = self.generateRequest('/Contacts/' + str(contact_id) + '/Addresses', 'GET', '')
                addresses = self.dictToList(json.loads(text))
                print 'PASS: getContactAddresses()'
                self.tests_passed += 1
                return addresses
            except:
                print 'FAIL: getContactAddresses()'
        else:
            text = self.generateRequest('/Contacts/' + str(contact_id) + '/Addresses', 'GET', '')
            addresses = self.dictToList(json.loads(text))
            return addresses
    
    def getContactContactInfos(self, contact_id, test = False):
        """
        Get ContactInfos linked to a contact
        """
        if self.version != '2.2':
            raise Exception('method only supported for version 2.2 API')
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Contacts/' + str(contact_id) + '/ContactInfos', 'GET', '')
                contactinfos = self.dictToList(json.loads(text))
                print 'PASS: getContactContactInfos()'
                self.tests_passed += 1
                return contactinfos
            except:
                print 'FAIL: getContactContactInfos()'
        else:
            text = self.generateRequest('/Contacts/' + str(contact_id) + '/ContactInfos', 'GET', '')
            contactinfos = self.dictToList(json.loads(text))
            return contactinfos

    def getContactEmails(self, contact_id, test = False):
        """
        Gets emails for a contact, identified by its record locator, returns a list of dictionaries
        """
        #
        # Get a contact's emails
        #
        # HTTP GET api.insight.ly/v2.2/Contacts/{id}/Emails
        #
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Contacts/' + str(contact_id) + '/Emails', 'GET', '')
                emails = self.dictToList(json.loads(text))
                print 'PASS: getContactEmails() found ' + str(len(emails)) + ' emails'
                self.tests_passed += 1
                return emails
            except:
                print 'FAIL: getContactEmails()'
        else:
            text = self.generateRequest('/Contacts/' + str(contact_id) + '/Emails', 'GET', '')
            emails = self.dictToList(json.loads(text))
            return emails
        
    def getContactEvents(self, contact_id, test = False):
        """
        Gets events linked to a contact
        """
        if self.version != '2.2':
            raise Exception('method only supported for version 2.2 API')
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Contacts/' + str(contact_id) + '/Events', 'GET', '')
                events = self.dictToList(json.loads(text))
                print 'PASS: getContactEvents()'
                self.tests_passed += 1
                return events
            except:
                print 'FAIL: getContactEvents()'
        else:
            text = self.generateRequest('/Contacts/' + str(contact_id) + '/Events', 'GET', '')
            events = self.dictToList(json.loads(text))
            return events
    
    def getContactFileAttachments(self, contact_id, test = False):
        """
        Gets files attached to a contact
        """
        if self.version != '2.2':
            raise Exception('method only supported for version 2.2 API')
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Contacts/' + str(contact_id) + '/FileAttachments', 'GET', '')
                file_attachments = self.dictToList(json.loads(text))
                print 'PASS: getContactFileAttachments()'
                self.tests_passed += 1
                return file_attachments
            except:
                print 'FAIL: getContactFileAttachments()'
        else:
            text = self.generateRequest('/Contacts/' + str(contact_id) + '/FileAttachments', 'GET', '')
            file_attachments = self.dictToList(json.loads(text))
            return file_attachments
    
    def getContactNotes(self, contact_id, test = False):
        """
        Gets a list of the notes attached to a contact, identified by its record locator. Returns a list of dictionaries.
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Contacts/' + str(contact_id) + '/Notes', 'GET', '')
                notes = self.dictToList(json.loads(text))
                print 'PASS: getContactNotes() found ' + str(len(notes)) + ' notes'
                self.tests_passed += 1
                return notes
            except:
                print 'FAIL: getContactNotes()'
        else:
            text = self.generateRequest('/Contacts/' + str(contact_id) + '/Notes', 'GET', '')
            notes = self.dictToList(json.loads(text))
            return notes
    
    def getContactTags(self, contact_id, test = False):
        """
        Gets a list of tags linked to a contact, returns a JSON list. 
        """
        if self.version != '2.2':
            raise Exception('method only supported for version 2.2 API')
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Contacts/' + str(contact_id) + '/Tags', 'GET', '')
                tags = self.dictToList(json.loads(text))
                print 'PASS: getContactTags()'
                self.tests_passed += 1
                return tags
            except:
                print 'FAIL: getContactTags()'
        else:
            text = self.generateRequest('/Contacts/' + str(contact_id) + '/Tags', 'GET', '')
            tags = self.dictToList(json.loads(text))
            return tags

        
    def getContactTasks(self, contact_id, test = False):
        """
        Gets a list of the tasks attached to a contact, identified by its record locator. Returns a list of dictionaries.
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Contacts/' + str(contact_id) + '/Tasks', 'GET', '')
                tasks = self.dictToList(json.loads(text))
                print 'PASS: getContactTasks() found ' + str(len(tasks)) + ' tasks'
                self.tests_passed += 1
                return tasks
            except:
                print 'FAIL: getContactTasks()'
        else:
            text = self.generateRequest('/Contacts/' + str(contact_id) + '/Tasks', 'GET', '')
            return self.dictToList(json.loads(text))
    
    def getCountries(self, test = False):
        """
        Gets a list of countries recognized by Insightly. Returns a list of dictionaries.
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Countries', 'GET', '')
                countries = json.loads(text)
                print 'PASS: getCountries() found ' + str(len(countries)) + ' countries'
                self.tests_passed += 1
                return countries
            except:
                print 'FAIL: getCountries()'
        else:
            text = self.generateRequest('/Countries', 'GET', '')
            countries = json.loads(text)
            return countries
    
    def getCurrencies(self, test = False):
        """
        Gets a list of currencies recognized by Insightly. Returns a list of dictionaries.
        """
        text = self.generateRequest('/Currencies', 'GET', '')
        currencies = json.loads(text)
        if test:
            try:
                print 'PASS: getCurrencies() found ' + str(len(currencies)) + ' supported currencies.'
                self.tests_run += 1
                self.tests_passed += 1
            except:
                self.tests_run += 1
        return currencies
    
    def getCustomFields(self, test = False):
        """
        Gets a list of custom fields, returns a list of dictionaries
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/CustomFields', 'GET', '')
                custom_fields = self.dictToList(json.loads(text))
                self.tests_passed += 1
                print 'PASS: getCustomFields() found ' + str(len(custom_fields)) + ' custom fields'
                return custom_fields
            except:
                print 'FAIL: getCustomFields()'
        else:
            text = self.generateRequest('/CustomFields', 'GET', '')
            custom_fields = self.dictToList(json.loads(text))
            return custom_fields
    
    def getCustomField(self, id, test = False):
        """
        Gets details for a custom field, identified by its record id. Returns a dictionary
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/CustomFields/' + str(id), 'GET', '')
                custom_field = json.loads(text)
                print 'PASS: getCustomField()'
                self.tests_passed += 1
                return custom_field
            except:
                print 'FAIL: getCustomField()'
        else:
            text = self.generateRequest('/CustomFields/' + str(id), 'GET', '')
            custom_field = json.loads(text)
            return custom_field            
    
    def getEmails(self, top=None, skip=None, orderby=None, filters=None, test = False):
        """
        Returns a list of emails for a resource id.
        
        This search method supports the OData operators: top, skip, orderby and filters
        """
        if test:
            self.tests_run += 1
            try:
                querystring = self.ODataQuery('', top=top, skip=skip, orderby=orderby, filters=None)
                text = self.generateRequest('/Emails' + querystring, 'GET','')
                emails = self.dictToList(json.loads(text))
                self.tests_passed += 1
                print 'PASS: getEmails() found ' + str(len(emails)) + ' emails'
                return emails
            except:
                print 'FAIL: getEmails()'
        else:
            querystring = self.ODataQuery('', top=top, skip=skip, orderby=orderby, filters=None)
            text = self.generateRequest('/Emails' + querystring, 'GET','')
            emails = self.dictToList(json.loads(text))
            return emails
        
    def getEmail(self, id, test = False):
        """
        Returns an invidivual email, identified by its record locator id
        
        Returns a dictionary as a response or raises an exception
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Emails/' + str(id), 'GET', '')
                email = json.loads(text)
                print 'PASS: getEmail()'
                self.tests_passed += 1
                return email
            except:
                print 'FAIL: getEmail()'
        else:
            text = self.generateRequest('/Emails/' + str(id), 'GET', '')
            email = json.loads(text)
            return email
        
    def deleteEmail(self,id, test = False):
        """
        Deletes an individual email, identified by its record locator id
        
        Returns True or raises an exception
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Emails/' + str(id), 'DELETE', '')
                print 'PASS: deleteEmail()'
                self.tests_passed += 1
                return True
            except:
                print 'FAIL: deleteEmail()'
        else:
            text = self.generateRequest('/Emails/' + str(id), 'DELETE', '')
            return True
    
    def getEmailComments(self, id, test = False):
        """
        Returns the comments attached to an email, identified by its record locator id
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Emails/' + str(id) + '/Comments')
                comments = self.dictToList(json.loads(text))
                print 'PASS: getEmailComments() found ' + str(len(comments)) + ' comments attached to a test email'
                self.tests_passed += 1
                return comments
            except:
                print 'FAIL: getEmailComments()'
        else:
            text = self.generateRequest('/Emails/' + str(id) + '/Comments')
            comments = self.dictToList(json.loads(text))
            return comments
        
    def addCommentToEmail(self, id, body, owner_user_id, test = False):
        """
        Adds a comment to an existing email, identified by its record locator id.
        
        The comment parameter is a dictionary containing the following fields:
        
        TODO: getting 400 responses, needed to debug
        """
        data = dict(
            BODY = body,
            OWNER_USER_ID = owner_user_id,
        )
        urldata = json.dumps(data)
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Emails/' + str(id) + '/Comments', 'POST', urldata)
                comment = json.loads(text)
                print 'PASS: addCommentToEmail()'
                self.tests_passed += 1
                return comment
            except:
                print 'FAIL: addCommentToEmail()'
        else:
            text = self.generateRequest('/Emails/' + str(id) + '/Comments', 'POST', urldata)
            comment = json.loads(text)
            return comment
    
    def addEvent(self, event, test = False):
        """
        Add or update an event in the calendar.
        
        NOTE: owner_user_id is required, and must point to a valid Insightly user id, if not you will get
        a 400 (bad request) error.
        """
        if type(event) is str:
            if event == 'sample':
                events = self.getEvents(top=1)
                return events[0]
        elif type(event) is dict:
            if test:
                self.tests_run += 1
                try:
                    if event.get('EVENT_ID', 0) > 0:
                        text = self.generateRequest('/Events', 'PUT', json.dumps(event))
                    else:
                        text = self.generateRequest('/Events', 'POST', json.dumps(event))
                    event = json.loads(text)
                    self.tests_passed += 1
                    print 'PASS: addEvent()'
                    return event
                except:
                    print 'FAIL: addEvent()'
            else:
                if event.get('EVENT_ID', 0) > 0:
                    text = self.generateRequest('/Events', 'PUT', json.dumps(event))
                else:
                    text = self.generateRequest('/Events', 'POST', json.dumps(event))
                return json.loads(text)
        else:
            raise Exception('The parameter event should be a dictionary with valid fields for an event object, or the string \'sample\' to request a sample object.')
    
    def deleteEvent(self, id, test = False):
        """
        Deletes an event, identified by its record id
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Events/' + str(id), 'DELETE', '')
                self.tests_passed += 1
                print 'PASS: deleteEvent()'
                return True
            except:
                print 'FAIL: deleteEvent()'
        else:
            text = self.generateRequest('/Events/' + str(id), 'DELETE', '')
            return True
        
    def getEvents(self, top=None, skip=None, orderby=None, filters=None, test = False):
        """
        Gets a calendar of upcoming events.
        
        This method supports OData filters:
        
        top = return first N records
        skip = skip the first N records
        orderby = order results, e.g.: orderby='START_DATE_UTC desc'
        filters = list of filters, e.g.: ['FIRST_NAME=\'Brian\'','LAST_NAME=\'McConnell\'']
        
        List is returned as a list of dictionaries.
        """
        if test:
            self.tests_run += 1
            try:
                querystring = self.ODataQuery('', top = top, skip=skip, orderby = orderby, filters = filters)
                text = self.generateRequest('/Events' + querystring, 'GET', '')
                events = self.dictToList(json.loads(text))
                print 'PASS: getEvents() found ' + str(len(events)) + ' events'
                self.tests_passed += 1
                return events
            except:
                print 'FAIL: getEvents()'
        else:
            querystring = self.ODataQuery('', top = top, skip=skip, orderby = orderby, filters = filters)
            text = self.generateRequest('/Events' + querystring, 'GET', '')
            return self.dictToList(json.loads(text))

    def getEvent(self, id, test = False):
        """
        gets an individual event, identified by its record id
        
        Returns a dictionary
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Events/' + str(id), 'GET', '')
                event = json.loads(text)
                print 'PASS: getEvent()'
                self.tests_passed += 1
                return event
            except:
                print 'FAIL: getEvent()'
        else:
            text = self.generateRequest('/Events/' + str(id), 'GET', '')
            event = json.loads(text)
            return event
    
    def addFileCategory(self, category, test=False):
        """
        Add/update a file category to your account. Expects a dictionary containing the category details.
        
        You can also call addFileCategory('sample') to request a sample object. 
        """
        if type(category) is str:
            if category == 'sample':
                categories = self.getFileCategories()
                return categories[0]
        if type(category) is not dict:
            raise Exception('category must be a dict')
        urldata = json.dumps(category)
        if test:
            self.tests_run += 1
            try:
                if category.get('CATEGORY_ID',None) is not None:
                    text = self.generateRequest('/FileCategories', 'PUT', urldata)
                else:
                    text = self.generateRequest('/FileCategories', 'POST', urldata)
                category = json.loads(text)
                print 'PASS: addFileCategory()'
                self.tests_passed += 1
                return category
            except:
                print 'FAIL: addFileCategory()'
        else:
            if category.get('CATEGORY_ID',None) is not None:
                text = self.generateRequest('/FileCategories', 'PUT', urldata)
            else:
                text = self.generateRequest('/FileCategories', 'POST', urldata)
            return json.loads(text)
    
    def deleteFileCategory(self, id, test = False):
        """
        Delete a file category, identified by its record id
        
        Returns True if successful or raises an exception
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/FileCategories/' + str(id), 'DELETE', '')
                self.tests_passed += 1
                print 'PASS: deleteFileCategory()'
                return True
            except:
                print 'FAIL: deleteFileCategory()'
        else:
            text = self.generateRequest('/FileCategories/' + str(id), 'DELETE', '')
            return True
    
    def getFileCategories(self, test = False):
        """
        Gets a list of file categories
        
        Returns a list of dictionaries
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/FileCategories', 'GET', '')
                categories = self.dictToList(json.loads(text))
                print 'PASS: getFileCategories() found ' + str(len(categories)) + ' file categories'
                self.tests_passed += 1
                return categories
            except:
                print 'FAIL: getFileCategories()'
        else:
            text = self.generateRequest('/FileCategories', 'GET', '')
            return self.dictToList(json.loads(text))
        
    def getFileCategory(self, id, test = False):
        """
        Gets a file category, identified by its record id
        
        Returns a dictionary
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/FileCategories/' + str(id), 'GET', '')
                category = json.loads(text)
                print 'PASS: getFileCategory()'
                self.tests_passed += 1
                return category
            except:
                print 'FAIL: getFileCategory()'
        else:
            text = self.generateRequest('/FileCategories/' + str(id), 'GET', '')
            return json.loads(text)
    
    def addNote(self, note, test = False):
        """
        Add/update a note, where the parameter note is a dictionary withthe required fields. To obtain a sample object, just call
        
        addNote('sample')
        
        The method returns a dictionary containing the object as it is stored on the server, or raises an exception if the update
        failed. If you receive a 400 (bad request) error it is probably because you are missing a required field, or are linking to
        another record improperly. 
        """
        if type(note) is str:
            if note == 'sample':
                note = self.getNotes(top=1)
                return note[0]
            else:
                raise Exception('note must be a dictionary with valid fields, or the string \'sample\' to request a sample object')
        elif type(note) is dict:
            if test:
                self.tests_run += 1
                try:
                    if note.get('NOTE_ID',0) > 0:
                        text = self.generateRequest('/Notes', 'PUT', json.dumps(note))
                    else:
                        text = self.generateRequest('/Notes', 'POST', json.dumps(note))
                    note = json.loads(text)
                    self.tests_passed += 1
                    print 'PASS: addNote()'
                    return note
                except:
                    print 'FAIL: addNote()'
            else:
                if note.get('NOTE_ID',0) > 0:
                    text = self.generateRequest('/Notes', 'PUT', json.dumps(note))
                else:
                    text = self.generateRequest('/Notes', 'POST', json.dumps(note))
                return json.loads(text)
        else:
            return
        
    def deleteNote(self, id, test = False):
        """
        Delete a note, identified by its record locator.
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Notes/' + str(id), 'DELETE', '')
                print 'PASS: deleteNote()'
                self.tests_passed += 1
                return True
            except:
                print 'FAIL: deleteNote()'
        else:
            text = self.generateRequest('/Notes/' + str(id), 'DELETE', '')
            return True
    
    def getNotes(self, top=None, skip=None, orderby=None, filters=None, test = False):
        """
        Gets a list of notes created by the user, returns a list of dictionaries
        
        This method supports the ODATA operators:
        
        top = return first N records
        skip = skip first N records
        orderby = order by statement (e.g. 'DATE_CREATED_UTC desc')
        filters = list of filter statements
        """
        if not test:
            querystring = self.ODataQuery('', top=top, skip=skip, orderby=orderby, filters=filters)
            text = self.generateRequest('/Notes' + querystring, 'GET', '')
            return self.dictToList(json.loads(text))
        else:
            self.tests_run += 1
            try:
                querystring = self.ODataQuery('', top=top, skip=skip, orderby=orderby, filters=filters)
                text = self.generateRequest('/Notes' + querystring, 'GET', '')
                notes = self.dictToList(json.loads(text))
                print 'PASS: getNotes() found ' + str(len(notes)) + ' notes'
                self.tests_passed += 1
                return notes
            except:
                print 'FAIL: getNotes()'
        
    def getNote(self, id, test = False):
        """
        Gets a note, identified by its record id. Returns a dictionary or raises an error.
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Notes/' + str(id), 'GET', '')
                note = json.loads(text)
                print 'PASS: getNote()'
                self.tests_passed += 1
                return note
            except:
                print 'FAIL: getNote()'
        else:
            text = self.generateRequest('/Notes/' + str(id), 'GET', '')
            note = json.loads(text)
            return note
    
    def getNoteComments(self, id, test = False):
        """
        Gets the comments attached to a note, identified by its record id. Returns a list of dictionaries.
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Notes/' + str(id) + '/Comments', 'GET', '')
                comments = self.dictToList(json.loads(text))
                print 'PASS: getNoteComments() found ' + str(len(comments)) + ' attached to a test note'
                self.tests_passed += 1
                return comments
            except:
                print 'FAIL: getNoteComments()'
        else:
            text = self.generateRequest('/Notes/' + str(id) + '/Comments', 'GET', '')
            comments = self.dictToList(json.loads(text))
            return comments
    
    def addNoteComment(self, id, comment, test = False):
        """
        Method not implemented yet
        """
        if type(comment) is str:
            if comment == 'sample':
                comment = dict(
                    COMMENT_ID = 0,
                    BODY = 'This is a comment.',
                    OWNER_USER_ID = 1,
                    DATE_CREATED_UTC = '2014-07-15 16:40:00',
                    DATE_UPDATED_UTC = '2014-07-15 16:40:00',
                )
                return comment
            else:
                raise Exception('The parameter comment should be a dictionary with the required fields, or the string \'sample\' to request a sample object.')
        elif type(comment) is dict:
            if test:
                self.tests_run += 1
                try:
                    text = self.generateRequest('/' + str(id) +'/Comments', 'POST', json.dumps(comment))
                    comment = json.loads(text)
                    self.tests_passed += 1
                    print 'PASS: addNoteComment()'
                    return comment
                except:
                    print 'FAIL: addNoteComment()'
            else:
                text = self.generateRequest('/' + str(id) +'/Comments', 'POST', json.dumps(comment))
                comment = json.loads(text)
        else:
            raise Exception('The parameter comment should be a dictionary with the required fields, or the string \'sample\' to request a sample object.')
    
    def addOpportunity(self, opportunity, test = True):
        """
        Add/update an opportunity in Insightly. This method expects a dictionary containing valid fields for an opportunity, or the string 'sample' to request a sample object. 
        """
        if type(opportunity) is str:
            if opportunity == 'sample':
                opportunities = self.getOpportunities(top=1)
                return opportunities[0]
            else:
                raise Exception('The parameter opportunity must be a dictionary with valid fields for an opportunity, or the string \'sample\' to request a sample object.')
        elif type(opportunity) is dict:
            if opportunity.get('OPPORTUNITY_STATE', None) is None:
                raise Exception('OPPORTUNITY_STATE (required field) is missing')
            if test:
                self.tests_run += 1
                try:
                    if opportunity.get('OPPORTUNITY_ID',0) > 0:
                        text = self.generateRequest('/Opportunities', 'PUT', json.dumps(opportunity))
                    else:
                        text = self.generateRequest('/Opportunities', 'POST', json.dumps(opportunity))
                    opportunity = json.loads(text)
                    print 'PASS: addOpportunity()'
                    self.tests_passed += 1
                    return opportunity
                except:
                    print 'FAIL: addOpportunity()'
            else:
                if opportunity.get('OPPORTUNITY_ID',0) > 0:
                    text = self.generateRequest('/Opportunities', 'PUT', json.dumps(opportunity))
                else:
                    text = self.generateRequest('/Opportunities', 'POST', json.dumps(opportunity))
                opportunity = json.loads(text)
                return opportunity
        else:
            raise Exception('The parameter opportunity must be a dictionary with valid fields for an opportunity, or the string \'sample\' to request a sample object.')
    
    def deleteOpportunity(self, id, test = False):
        """
        Deletes an opportunity, identified by its record id. Returns True if successful, or raises an exception
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Opportunities/' + str(id), 'DELETE', '')
                self.tests_passed += 1
                print 'PASS: deleteOpportunity()'
                return True
            except:
                print 'FAIL: deleteOpportunity()'
        else:
            text = self.generateRequest('/Opportunities/' + str(id), 'DELETE', '')
            return True

    
    def getOpportunities(self, ids=None, tag=None, top=None, skip=None, orderby=None, filters=None, test=False):
        """
        Gets a list of opportunities
        
        This method recognizes the OData operators:
        top = return the first N records
        skip = skip the first N records
        orderby = orderby clause, e.g.: orderby='DATE_UPDATED_UTC desc'
        filters = list of OData filter statements
        """
        if test:
            self.tests_run += 1
            try:
                querystring = self.ODataQuery('', top=top, skip=skip, orderby=orderby, filters=filters)
                text = self.generateRequest('/Opportunities' + querystring, 'GET', '')
                opportunities = self.dictToList(json.loads(text))
                print 'PASS: getOpportunities() found ' + str(len(opportunities)) + ' opportunities'
                self.tests_passed += 1
            except:
                print 'FAIL: getOpportunities()'
        else:
            querystring = self.ODataQuery('', top=top, skip=skip, orderby=orderby, filters=filters)
            text = self.generateRequest('/Opportunities' + querystring, 'GET', '')
            return self.dictToList(json.loads(text))
    
    def getOpportunity(self, id, test = False):
        """
        Gets an opportunity's details, identified by its record id, returns a dictionary
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Opportunities/' + str(id), 'GET', '')
                opportunity = json.loads(text)
                print 'PASS: getOpportunity()'
                self.tests_passed += 1
                return opportunity
            except:
                print 'FAIL: getOpportunity()'
        else:
            text = self.generateRequest('/Opportunities/' + str(id), 'GET', '')
            opportunity = json.loads(text)
            return opportunity
    
    def getOpportunityStateHistory(self, id, test = False):
        """
        Gets the history of states and reasons for an opportunity.
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Opportunities/' + str(id) + '/StateHistory', 'GET', '')
                history = self.dictToList(json.loads(text))
                print 'PASS: getOpportunityStateHistory()'
                self.tests_passed += 1
                return history
            except:
                print 'FAIL: getOpportunityStateHistory()'
        else:
            text = self.generateRequest('/Opportunities/' + str(id) + '/StateHistory', 'GET', '')
            history = self.dictToList(json.loads(text))
            return history
    
    def getOpportunityEmails(self, id, test = False):
        """
        Gets the emails linked to an opportunity
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Opportunities/' + str(id) + '/Emails', 'GET', '')
                emails = self.dictToList(json.loads(text))
                print 'PASS: getOpportunityEmails()'
                self.tests_passed += 1
                return emails
            except:
                print 'FAIL: getOpportunityEmails()'
        else:
            text = self.generateRequest('/Opportunities/' + str(id) + '/Emails', 'GET', '')
            emails = self.dictToList(json.loads(text))
            return emails
            
    def getOpportunityNotes(self, id, test = False):
        """
        Gets the notes linked to an opportunity
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Opportunities/' + str(id) + '/Notes', 'GET', '')
                notes = self.dictToList(json.loads(text))
                print 'PASS: getOpportunityNotes()'
                self.tests_passed += 1
                return notes
            except:
                print 'FAIL: getOpportunityNotes()'
        else:
            text = self.generateRequest('/Opportunities/' + str(id) + '/Notes', 'GET', '')
            notes = self.dictToList(json.loads(text))
            return notes
    
    def getOpportunityTasks(self, id, test = False):
        """
        Gets the tasks linked to an opportunity
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Opportunities/' + str(id) + '/Tasks', 'GET', '')
                tasks = self.dictToList(json.loads(text))
                self.tests_passed += 1
                print 'PASS: getOpportunityTasks()'
                return tasks
            except:
                print 'FAIL: getOpportunityTasks()'
        else:
            text = self.generateRequest('/Opportunities/' + str(id) + '/Tasks', 'GET', '')
            tasks = self.dictToList(json.loads(text))
            return tasks
        
    def addOpportunityCategory(self, category, test = False):
        """
        Add/update an opportunity category.
        """
        if type(category) is str:
            if category == 'sample':
                categories = self.getOpportunityCategories()
                return categories[0]
            else:
                raise Exception('category must be a dictionary, or \'sample\' to request a sample object')
        else:
            if test:
                self.tests_run += 1
                try:
                    if category.get('CATEGORY_ID', 0) > 0:
                        text = self.generateRequest('/OpportunityCategories', 'PUT', json.dumps(category))
                    else:
                        text = self.generateRequest('/OpportunityCategories', 'POST', json.dumps(category))
                    category = json.loads(text)
                    print 'PASS: addOpportunityCategory()'
                    self.tests_passed += 1
                    return category
                except:
                    print 'FAIL: addOpportunityCategory()'
            else:
                if category.get('CATEGORY_ID', 0) > 0:
                    text = self.generateRequest('/OpportunityCategories', 'PUT', json.dumps(category))
                else:
                    text = self.generateRequest('/OpportunityCategories', 'POST', json.dumps(category))
                category = json.loads(text)
                return category
    
    def deleteOpportunityCategory(self, id, test = False):
        """
        Deletes an opportunity category. Returns True or raises an exception.
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/OpportunityCategories/' + str(id), 'DELETE', '')
                print 'PASS: deleteOpportunityCategory()'
                self.tests_passed += 1
                return True
            except:
                print 'FAIL: deleteOpportunityCategory()'
        else:
            text = self.generateRequest('/OpportunityCategories/' + str(id), 'DELETE', '')
            return True
    
    def getOpportunityCategory(self, id, test = False):
        """
        Gets an opportunity category, identified by its record id.
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/OpportunityCategories/' + str(id), 'GET', '')
                category = json.loads(text)
                print 'PASS: getOpportunityCategory()'
                self.tests_passed += 1
                return category
            except:
                print 'FAIL: getOpportunityCategory()'
        else:
            text = self.generateRequest('/OpportunityCategories/' + str(id), 'GET', '')
            category = json.loads(text)
            return category
    
    def getOpportunityCategories(self, test = False):
        """
        Gets a list of opportunity categories.
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/OpportunityCategories', 'GET', '')
                categories = self.dictToList(json.loads(text))
                print 'PASS: getOpportunityCategories()'
                self.tests_passed += 1
                return categories
            except:
                print 'FAIL: getOpportunityCategories()'
        else:
            text = self.generateRequest('/OpportunityCategories', 'GET', '')
            categories = self.dictToList(json.loads(text))
            return categories
    
    def getOpportunityStateReasons(self, test = False):
        """
        Gets a list of opportunity state reasons, returns a list of dictionaries
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/OpportunityStateReasons', 'GET', '')
                reasons = self.dictToList(json.loads(text))
                print 'PASS: getOpportunityStateReasons()'
                self.tests_passed += 1
                return reasons
            except:
                print 'FAIL: getOpportunityStateReasons()'
        else:
            text = self.generateRequest('/OpportunityStateReasons', 'GET', '')
            reasons = self.dictToList(json.loads(text))
            return reasons
    
    def addOrganization(self, organization):
        """
        Add/update an organization.
        
        Expects a dictionary with valid fields for an organization. Returns a dictionary containing the item as stored on the server, or raises an exception.
        
        To request a sample item, call addOrganization('sample')
        """
        if type(organization) is str:
            if organization == 'sample':
                organizations = self.getOrganizations(top=1)
                return organizations[0]
            else:
                raise Exception('The parameter organization must be a dictionary with valid fields for an organization, or the string \'sample\' to request a sample object.')
        elif type(organization) is dict:
            if organization.get('ORGANIZATION_ID', 0) > 0:
                text = self.generateRequest('/Organisations', 'PUT', json.dumps(organization))
            else:
                text = self.generateRequest('/Organisations', 'POST', json.dumps(organization))
            return json.loads(text)
        else:
            raise Exception('The parameter organization must be a dictionary with valid fields for an organization, or the string \'sample\' to request a sample object.')
    
    def deleteOrganization(self, id):
        """
        Delete an organization, identified by its record locator
        """
        text = self.generateRequest('/Organisations/' + str(id), 'DELETE', '')
        return True
    
    def getOrganizations(self, ids=None, domain=None, tag=None, top=None, skip=None, orderby=None, filters=None):
        """
        Gets a list of organizations, returns a list of dictionaries
        
        This method recognizes the OData operators:
        
        top = return the first N filters
        skip = skip the first N filters
        orderby = orderby clause, e.g. orderby='DATE_UPDATED_UTC desc'
        filters = list of OData filter statements
        """
        querystring = ''
        if domain is not None:
            querystring += '?domain=' + urllib.quote_plus(domain)
        if tag is not None:
            if len(querystring) > 0:
                querystring += '&tag=' + urllib.quote_plus(tag)
            else:
                querystring += '?tag=' + urllib.quote_plus(tag)
        if ids is not None:
            ids = string.replace(ids,' ','')
            if len(querystring) > 0:
                querystring += '?ids=' + ids
            else:
                querystring += '&ids=' + ids
        querystring = self.ODataQuery(querystring, top=top, skip=skip, orderby=orderby, filters=filters)
        text = self.generateRequest('/Organisations' + querystring, 'GET', '')
        return self.dictToList(json.loads(text))
        
    def getOrganization(self, id):
        """
        Gets an organization, identified by its record id, returns a dictionary
        """
        text = self.generateRequest('/Organisations/' + str(id), 'GET', '')
        return json.loads(text)
    
    def getOrganizationEmails(self, id):
        """
        Gets a list of emails attached to an organization, identified by its record id, returns a list of dictionaries
        """
        text = self.generateRequest('/Organisations/' + str(id) + '/Emails', 'GET', '')
        return self.dictToList(json.loads(text))
    
    def getOrganizationNotes(self, id):
        """
        Gets a list of notes attached to an organization, identified by its record id, returns a list of dictionaries
        """
        text = self.generateRequest('/Organisations/' + str(id) + '/Notes', 'GET', '')
        return self.dictToList(json.loads(text))
    
    def getOrganizationTasks(self, id):
        """
        Gets a list of tasks attached to an organization, identified by its record id, returns a list of dictionaries
        """
        text = self.generateRequest('/Organisations/' + str(id) + '/Tasks', 'GET', '')
        return self.dictToList(json.loads(text))
    
    #
    # Following are methods for pipelines
    #
    
    def getPipelines(self, test = False):
        """
        Gets a list of pipelines
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Pipelines', 'GET', '')
                pipelines = self.dictToList(json.loads(text))
                print 'PASS: getPipelines() found ' + str(len(pipelines)) + ' pipelines'
                self.tests_passed += 1
                return pipelines
            except:
                print 'FAIL: getPipelines()'
        else:
            text = self.generateRequest('/Pipelines', 'GET', '')
            return self.dictToList(json.loads(text))

    
    def getPipeline(self, id, test = False):
        """
        Gets details for a pipeline, identified by its unique record id
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Pipelines/' + str(id), 'GET', '')
                pipeline = json.loads(text)
                self.tests_passed += 1
                print 'PASS: getPipeline()'
                return pipeline
            except:
                print 'FAIL: getPipeline()'
        else:
            text = self.generateRequest('/Pipelines/' + str(id), 'GET', '')
            return json.loads(text)
    #
    # Following are methods for obtaining pipeline stages
    #
    
    def getPipelineStages(self, test = False):
        """
        Gets a list of pipeline stages
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/PipelineStages','GET','')
                stages = self.dictToList(json.loads(text))
                print 'PASS: getPipelineStages() found ' + str(len(stages)) + ' stages'
                self.tests_passed += 1
                return stages
            except:
                print 'FAIL: getPipelineStages()'
        else:
            text = self.generateRequest('/PipelineStages','GET','')
            return self.dictToList(json.loads(text))
        
    def getPipelineStage(self, id, test = False):
        """
        Gets a pipeline stage, identified by its unique record id
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/PipelineStages/' + str(id), 'GET','')
                stage = json.loads(text)
                print 'PASS: getPipelineStage()'
                self.tests_passed += 1
                return stage
            except:
                print 'FAIL: getPipelineStage()'
        else:
            text = self.generateRequest('/PipelineStages/' + str(id), 'GET','')
            return json.loads(text)
    
    #
    # Following are methods for managing project categories
    #
    
    def getProjectCategories(self, test = False):
        """
        Gets a list of project categories
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/ProjectCategories', 'GET','')
                categories = self.dictToList(json.loads(text))
                self.tests_passed += 1
                print 'PASS: getProjectCategories() found ' + str(len(categories)) + ' project categories'
            except:
                print 'FAIL: getProjectCategories()'
        else:
            text = self.generateRequest('/ProjectCategories', 'GET','')
            return self.dictToList(json.loads(text))
    
    def getProjectCategory(self, id, test = False):
        """
        Gets a project category, identified by its unique record id
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/ProjectCategories/' + str(id), 'GET', '')
                category = json.loads(text)
                self.tests_passed += 1
                print 'PASS: getProjectCategory()'
                return category
            except:
                print 'FAIL: getProjectCategory()'
        else:
            text = self.generateRequest('/ProjectCategories/' + str(id), 'GET', '')
            return json.loads(text)
    
    def addProjectCategory(self, category, test = False):
        """
        Add/update a project category. The parameter category should be a dictionary containing the project category details, or
        the string 'sample' to request a sample object. To add a new project category, just set the CATEGORY_ID to 0 or omit it. 
        """
        if type(category) is str:
            if category == 'sample':
                categories = self.getProjectCategories()
                return categories[0]
            else:
                raise Exception('category must be a dictionary, or \'sample\' to request a sample object')
        else:
            if test:
                self.tests_run += 1
                try:
                    if category.get('CATEGORY_ID', 0) > 0:
                        text = self.generateRequest('/ProjectCategories', 'PUT', json.dumps(category))
                    else:
                        text = self.generateRequest('/ProjectCategories', 'POST', json.dumps(category))
                    category = json.loads(text)
                    print 'PASS: addProjectCategory()'
                    self.tests_passed += 1
                    return category
                except:
                    print 'FAIL: addProjectCategory()'
            else:
                if category.get('CATEGORY_ID', 0) > 0:
                    text = self.generateRequest('/ProjectCategories', 'PUT', json.dumps(category))
                else:
                    text = self.generateRequest('/ProjectCategories', 'POST', json.dumps(category))
                return json.loads(text)
    
    def deleteProjectCategory(self, id, test = False):
        """
        Deletes a project category, returns True if successful or raises an exception
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/ProjectCategories/' + str(id), 'DELETE', '')
                self.tests_passed += 1
                print 'PASS: deleteProjectCategory()'
                return True
            except:
                print 'FAIL: deleteProjectCategory()'
        else:
            text = self.generateRequest('/ProjectCategories/' + str(id), 'DELETE', '')
            return True
    
    #
    # Following are methods use to list and manage Insightly projects
    # 
    
    def addProject(self, project):
        """
        Add update a project. The parameter project should be a dictionary containing the project details, or
        the string 'sample', to request a sample object. 
        """
        if type(project) is str:
            if project == 'sample':
                projects = self.getProjects(top=1)
                return projects[0]
            else:
                raise Exception('project must be a dictionary containing valid project data fields, or the string \'sample\' to request a sample object')
        else:
            if project.get('PROJECT_ID', 0) > 0:
                text = self.generateRequest('/Projects', 'PUT', json.dumps(project))
            else:
                text = self.generateRequest('/Projects', 'POST', json.dumps(project))
            return json.loads(text)
    
    def deleteProject(self, id):
        """
        Deletes a project, identified by its record id. Returns True if successful, or raises an exception.
        """
        text = self.generateRequest('/Projects/' + str(id), 'DELETE', '')
        return True
    
    def getProject(self, id):
        """
        Gets a project's details, identified by its record id, returns a dictionary
        """
        text = self.generateRequest('/Projects/' + str(id), 'GET', '')
        return json.loads(text)
    
    def getProjects(self, top=None, skip=None, orderby=None, filters=None, test = False):
        """
        Gets a list of projects, returns a list of dictionaries. This method supports the OData operators:
        
        top = return the first N records
        skip = skip the first N records
        orderby = orderby clause, eg. orderby='DATE_UPDATED_UTC desc'
        filters = list of OData filter statements
        """
        if test:
            self.tests_run += 1
            try:
                querystring = self.ODataQuery('', top=top, skip=skip, orderby=orderby, filters=filters)
                text = self.generateRequest('/Projects' + querystring, 'GET', '')
                projects = self.dictToList(json.loads(text))
                print 'PASS: getProjects() found ' + str(len(projects)) + ' projects'
                self.tests_passed += 1
                return projects
            except:
                print 'FAIL: getProjects()'
        else:
            querystring = self.ODataQuery('', top=top, skip=skip, orderby=orderby, filters=filters)
            text = self.generateRequest('/Projects' + querystring, 'GET', '')
            return self.dictToList(json.loads(text))
    
    def getProjectEmails(self, id, test = False):
        """
        Gets a list of emails attached to a project, identified by its record id, returns a list of dictionaries
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Projects/' + str(id) + '/Emails', 'GET', '')
                emails = self.dictToList(json.loads(text))
                print 'PASS: getProjectEmails() found ' + str(len(emails)) + ' emails attached to project'
                self.tests_passed += 1
                return emails
            except:
                print 'FAIL: getProjectEmails()'
        else:
            text = self.generateRequest('/Projects/' + str(id) + '/Emails', 'GET', '')
            return self.dictToList(json.loads(text))

    def getProjectNotes(self, id, test = False):
        """
        Gets a list of notes attached to a project, identified by its record id, returns a list of dictionaries
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Projects/' + str(id) + '/Notes', 'GET', '')
                notes = self.dictToList(json.loads(text))
                print 'PASS: getProjectNotes() found ' + str(len(notes)) + ' notes attached to project'
                self.tests_passed += 1
                return notes
            except:
                print 'FAIL: getProjectNotes()'
        else:
            text = self.generateRequest('/Projects/' + str(id) + '/Notes', 'GET', '')
            return self.dictToList(json.loads(text))
    
    def getProjectTasks(self, id, test = False):
        """
        Gets a list of tasks attached to a project, identified by its record id, returns a list of dictionaries
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Projects/' + str(id) + '/Tasks', 'GET', '')
                tasks = self.dictToList(json.loads(text))
                print 'PASS: getProjectTasks() found ' + str(len(tasks)) + ' tasks attached to project'
                self.tests_passed += 1
                return tasks
            except:
                print 'FAIL: getProjectTasks()'
        else:
            text = self.generateRequest('/Projects/' + str(id) + '/Tasks', 'GET', '')
            return self.dictToList(json.loads(text))
    
    #
    # Following are methods related to relationships between contacts and organizations
    #
    
    def getRelationships(self, test=False):
        """
        Gets a list of relationships.
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Relationships', 'GET', '')
                relationships = self.dictToList(json.loads(text))
                print 'PASS: getRelationships() found ' + str(len(relationships)) + ' relationships'
                self.tests_passed += 1
                return relationships
            except:
                print 'FAIL: getRelationships()'
        else:
            text = self.generateRequest('/Relationships', 'GET', '')
            return self.dictToList(json.loads(text))
        
    #
    # Following are methods related to tags
    #
    
    def getTags(self, id):
        """
        Gets a list of tags for a parent object
        """
        text = self.generateRequest('/Tags/' + str(id), 'GET', '')
        self.dictToList(json.loads(text))
        
    #
    # Following are methods related to tasks, and items attached to them
    #
    
    def addTask(self, task):
        """
        Add/update a task on Insightly. Submit the task details as a dictionary.
        
        To get a sample dictionary, call addTask('sample')
        
        To add a new task to Insightly, set the TASK_ID to 0. 
        """
        if type(task) is str:
            if task == 'sample':
                tasks = self.getTasks(top=1)
                return tasks[0]
            else:
                raise Exception('task must be a dictionary with valid task data fields, or the string \'sample\' to request a sample object')
        else:
            if task.get('TASK_ID',0) > 0:
                text = self.generateRequest('/Tasks', 'PUT', json.dumps(task))
            else:
                text = self.generateRequest('/Tasks', 'POST', json.dumps(task))
            return json.loads(text)
    
    def deleteTask(self, id):
        """
        Deletes a task, identified by its record ID, returns True if successful or raises an exception
        """
        text = self.generateRequest('/Tasks/' + str(id), 'DELETE', '')
        return True

    def getTasks(self, ids=None, top=None, skip=None, orderby=None, filters=None, test = False):
        """
        Gets a list of tasks, expects the optional parameter ids, which contains a list of task ids
        
        This method also recognizes the OData operators:
        
        top = return the first N records
        skip = skip the first N records
        orderby = orderby statement, example 'TITLE desc'
        filters = list of filter statements, example ['TITLE=\'Foo\'', 'BODY=\'Bar\'']
        """
        querystring = self.ODataQuery('', top=top, skip=skip, orderby=orderby, filters=filters)
        if ids is not None:
            if type(ids) is not list:
                raise Exception('Parameter ids must be a list')
                return
            else:
                querystring += '?ids='
                for i in ids:
                    querystring += i + ','
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Tasks' + querystring, 'GET', '')
                tasks = self.dictToList(json.loads(text))
                print 'PASS: getTasks() found ' + str(len(tasks)) + ' tasks'
                self.tests_passed += 1
                return tasks
            except:
                print 'FAIL: getTasks()'
        else:
            text = self.generateRequest('/Tasks' + querystring, 'GET', '')
            return self.dictToList(json.loads(text))
    
    def getTask(self, id):
        """
        Gets a task, identified by its record id
        """
        text = self.generateRequest('/Tasks/' + str(id), 'GET', '')
        return json.loads(text)
    
    def getTaskComments(self, id):
        """
        Gets a list of comments attached to a task, identified by its record id, returns a list of dictionaries
        """
        text = self.generateRequest('/Tasks/' + str(id) + '/Comments', 'GET', '')
        return self.dictToList(json.loads(text))
    
    def addTaskComment(self, id, comment):
        """
        Adds a comment to a task, the comment dictionary should have the following fields:
        
        COMMENT_ID = 0
        BODY = comment text
        OWNER_USER_ID = the comment author's Insightly user ID (numeric)
        
        NOTE: this function is not yet 100%, going over details of data expected with engineering.
        """
        json = json.dumps(comment)
        text = self.generateRequest('/Tasks/' + str(id) + '/Comments', 'POST', json)
        return json.loads(text)
    #
    # Following are methods for managing team members
    #
    
    def getTeamMembers(self, id, test = False):
        """
        Gets a list of team members, returns a list of dictionaries
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/TeamMembers?teamid=' + str(id), 'GET', '')
                teammembers = json.loads(text)
                self.tests_passed += 1
                print 'PASS: getTeamMembers() found ' + str(len(teammembers)) + ' team members'
            except:
                print 'FAIL: getTeamMembers()'
        text = self.generateRequest('/TeamMembers?teamid=' + str(id), 'GET', '')
        return json.loads(text)
    
    def getTeamMember(self, id, test = False):
        """
        Gets a team member's details
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/TeamMembers/' + str(id), 'GET', '')
                teammember = json.loads(text)
                print 'PASS: getTeamMemeber()'
                self.tests_passed += 1
                return teammember
            except:
                print 'FAIL: getTeamMember()'
        else:
            text = self.generateRequest('/TeamMembers/' + str(id), 'GET', '')
            return json.loads(text)
    
    def addTeamMember(self, team_member):
        """
        Add a team member.
        
        The parameter team_member should be a dictionary with valid fields, or the string 'sample' to request a sample object.
        """
        if type(team_member) is str:
            if team_member == 'sample':
                team_member = dict(
                    PERMISSION_ID = 1,
                    TEAM_ID=1,
                    MEMBER_USER_ID=1,
                    MEMBER_TEAM_ID=1,
                )
                return team_member
            else:
                raise Exception('team_member must be a dictionary with valid fields, or a string \'sample\' to request a sample object.')
        else:
            if type(team_member) is dict:
                text = self.generateRequest('/TeamMembers', 'POST', json.dumps(team_member))
                return json.loads(text)
            else:
                raise Exception('team_member must be a dictionary with valid fields, or a string \'sample\' to request a sample object.')
    
    def deleteTeamMember(self, id):
        """
        Deletes a team member, identified by their record id. Returns True if successful or raises an exception
        """
        text = self.generateRequest('/TeamMembers/' + str(id), 'DELETE', '')
        return True
    
    def updateTeamMember(self, team_member):
        """
        Update a team member.
        
        team_member should be a dictionary with valid fields, or the string 'sample' to request a sample object
        """
        if type(team_member) is str:
            if team_member == 'sample':
                team_member = dict(
                    PERMISSION_ID = 1,
                    TEAM_ID=1,
                    MEMBER_USER_ID=1,
                    MEMBER_TEAM_ID=1,
                )
                return team_member
            else:
                raise Exception('team_member must be a dictionary with valid fields, or a string \'sample\' to request a sample object.')
        else:
            if type(team_member) is dict:
                text = self.generateRequest('/TeamMembers', 'PUT', json.dumps(team_member))
                return json.loads(text)
            else:
                raise Exception('team_member must be a dictionary with valid fields, or a string \'sample\' to request a sample object.')
    
    # 
    # Following are methods related to Teams 
    # 
    
    def getTeams(self, top=None, skip=None, orderby=None, filters=None, test = False):
        """
        Gets a list of teams, returns a list of dictionaries
        """
        if test:
            self.tests_run += 1
            try:
                querystring = self.ODataQuery('', top=top, skip=skip, orderby=orderby, filters=filters)
                text = self.generateRequest('/Teams' + querystring, 'GET', '')
                teams = json.loads(text)
                print 'PASS: getTeams() found ' + str(len(teams)) + ' teams'
                self.tests_passed += 1
                return teams
            except:
                print 'FAIL: getTeams()'
        else:
            querystring = self.ODataQuery('', top=top, skip=skip, orderby=orderby, filters=filters)
            text = self.generateRequest('/Teams' + querystring, 'GET', '')
            return json.loads(text)

    def getTeam(self, id, test = False):
        """
        Gets a team, returns a dictionary
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Teams/' + str(id), 'GET', '')
                team = json.loads(text)
                print 'PASS: getTeam()'
                self.tests_passed += 1
                return team
            except:
                print 'FAIL: getTeam()'
        else:
            text = self.generateRequest('/Teams/' + str(id), 'GET', '')
            return json.loads(text)
        
    def addTeam(self, team):
        """
        Add/update a team on Insightly.
        
        The parameter team is a dictionary containing the details and team members. To get a sample object to work with
        just call addTeam('sample')
        
        NOTE: you will get a 400 error (bad request) if you do not include a valid list of team members
        """
        if type(team) is str:
            if string.lower(team) == 'sample':
                teams = self.getTeams(top=1)
                return teams[0]
            else:
                raise Exception('team must be a dictionary or \'sample\' (to obtain a sample object)')
        else:
            if type(team) is dict:
                urldata = json.dumps(team)
                if team.get('TEAM_ID',0) > 0:
                    text = self.generateRequest('/Teams', 'PUT', urldata)
                else:
                    text = self.generateRequest('/Teams', 'POST', urldata)
                return json.loads(text)
            else:
                raise Exception('team must be a dictionary or \'sample\' (to obtain a sample object)')
    
    def deleteTeam(self, id, test = False):
        """
        Deletes a team, returns True if successful, or raises an exception
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Teams/' + str(id), 'DELETE', '')
                print 'PASS: deleteTeam()'
                self.tests_passed += 1
                return True
            except:
                print 'FAIL: deleteTeam()'
        else:
            text = self.generateRequest('/Teams/' + str(id), 'DELETE', '')
            return True
        
    #
    # Following is a list of methods for accessing user information. These methods are read-only. 
    #
    
    def getUsers(self, test = False):
        """
        Gets a list of users for this account, returns a list of dictionaries
        """
        if test:
            try:
                text = self.generateRequest('/Users', 'GET', '')
                users = json.loads(text)
                print 'PASS: getUsers() : found ' + str(len(users)) + ' users'
                self.tests_run += 1
                self.tests_passed += 1
                return users
            except:
                print 'FAIL: getUsers()'
                self.tests_run += 1
        else:
            text = self.generateRequest('/Users', 'GET', '')
            return json.loads(text)
    
    def getUser(self, id, test = False):
        """
        Gets an individual user's details
        """
        if test:
            self.tests_run += 1
            try:
                text = self.generateRequest('/Users/' + str(id), 'GET', '')
                user = json.loads(text)
                print 'PASS: getUser()'
                self.tests_passed += 1
            except:
                print 'FAIL: getUser()'
        else:
            text = self.generateRequest('/Users/' + str(id), 'GET', '')
            return json.loads(text)