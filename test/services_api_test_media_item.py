import unittest
import json
import flask
import friendsNet.resources as resources
import friendsNet.database as database

DB_PATH = 'db/friendsNet_test.db'
ENGINE = database.Engine(DB_PATH)

COLLECTION_JSON = "application/vnd.collection+json"
HAL_JSON = "application/hal+json"

MEDIA_ITEM_PROFILE = "/profiles/media_item-profile"

#Tell Flask that I am running it in testing mode.
resources.app.config['TESTING'] = True
#Necessary for correct translation in url_for
resources.app.config['SERVER_NAME'] = 'localhost:5000'

#Database Engine utilized in our testing
resources.app.config.update({'Engine': ENGINE})

class ResourcesAPITestCase(unittest.TestCase):
    #INITIATION AND TEARDOWN METHODS
    @classmethod
    def setUpClass(cls):
        ''' Creates the database structure. Removes first any preexisting database file.'''
        print "Testing ", cls.__name__
        ENGINE.remove_database()
        ENGINE.create_tables()

    @classmethod
    def tearDownClass(cls):
        '''Remove the testing database.'''
        print "Testing ENDED for ", cls.__name__
        ENGINE.remove_database()

    def setUp(self):
        '''Populates the database.'''
        #This method loads the initial values from friendsNet_data_db.sql
        ENGINE.populate_tables()
        #Activate app_context for using url_for
        self.app_context = resources.app.app_context()
        self.app_context.push()
        #Create a test client
        self.client = resources.app.test_client()

    def tearDown(self):
        '''
        Remove all records from database.
        '''
        ENGINE.clear()
        self.app_context.pop()

class MediaItemTestCase(ResourcesAPITestCase):

    resp_get = {
        "id" : 1,
        "media_item_type" : 0,
        "url" : "/friendsNet/media_uploads/media1.jpg",
        "description" : "Flowers are wonderful!",
        "_links" : {
            "self" : {"href" : "/friendsNet/api/media/1/", "profile" : "/profiles/media_item-profile"},
            "media list" : {"href" : "/friendsNet/api/media/"}
        },
        "template" : {
            "data" : [
                {"name" : "description", "value" : "", "prompt" : "Media item description", "required" : "false"}
            ]
        }
    }

    media_patch_correct = {
        "template" : {
            "data" : [
                {"name" : "description", "value" : "New description!"}
            ]
        }
    }

    media_patch_empty = {
        "template" : {
            "data" : []
        }
    }

    def setUp(self):
        super(MediaItemTestCase, self).setUp()
        self.url = resources.api.url_for(resources.Media_item, media_id = 1, _external = False)
        self.url_wrong = resources.api.url_for(resources.Media_item, media_id = 999, _external = False)

#TEST URL
    def test_url(self):
        #Checks that the URL points to the right resource
        _url = '/friendsNet/api/media/1/'
        print '('+self.test_url.__name__+')', self.test_url.__doc__
        with resources.app.test_request_context(_url):
            rule = flask.request.url_rule
            view_point = resources.app.view_functions[rule.endpoint].view_class
            self.assertEquals(view_point, resources.Media_item)

    def test_wrong_url(self):
        #Checks that GET Friendship returns correct status code if given a wrong id
        resp = self.client.get(self.url_wrong, headers = {"Accept" : HAL_JSON})
        self.assertEquals(resp.status_code, 404)
        data = json.loads(resp.data)

        href = data["resource_url"]                         #test HREF
        self.assertEquals(href, self.url_wrong)

        error = data["code"]
        self.assertEquals(error, 404)

#TEST GET
#200 + MIMETYPE & PROFILE
    def test_get_media_item(self):
        print '('+self.test_get_media_item.__name__+')', self.test_get_media_item.__doc__
        with resources.app.test_client() as client:
            resp = client.get(self.url, headers = {"Accept" : HAL_JSON})
            self.assertEquals(resp.status_code, 200)
            data = json.loads(resp.data)

            self.assertEquals(self.resp_get, data)
            self.assertEqual(resp.headers.get("Content-Type", None), HAL_JSON)


#404
    def test_get_not_existing_media_item(self):
        print '('+self.test_get_not_existing_media_item.__name__+')', self.test_get_not_existing_media_item.__doc__
        with resources.app.test_client() as client:
            resp = client.get(self.url_wrong, headers = {"Accept" : HAL_JSON})
            self.assertEquals(resp.status_code, 404)

#TEST PATCH
#204
    def test_patch_media_item(self):
        print '('+self.test_patch_media_item.__name__+')', self.test_patch_media_item.__doc__
        resp = self.client.patch(self.url, data = json.dumps(self.media_patch_correct), headers = {"Content-Type" : COLLECTION_JSON})
        self.assertEquals(resp.status_code, 204)

        resp2 = self.client.get(self.url, headers = {"Accept" : HAL_JSON})
        self.assertEquals(resp2.status_code, 200)
        data = json.loads(resp2.data)
        new_value = data["description"]
        self.assertEquals(new_value, self.media_patch_correct["template"]["data"][0]["value"])

#PATCH EMPTY
    def test_patch_empty_media_item(self):
        print '('+self.test_patch_empty_media_item.__name__+')', self.test_patch_empty_media_item.__doc__
        resp = self.client.patch(self.url, data = json.dumps(self.media_patch_empty), headers = {"Content-Type" : COLLECTION_JSON})
        self.assertEquals(resp.status_code, 204)

#404
    def test_patch_not_existing_media_item(self):
        print '('+self.test_patch_not_existing_media_item.__name__+')', self.test_patch_not_existing_media_item.__doc__
        resp = self.client.patch(self.url_wrong, data = json.dumps(self.media_patch_correct), headers = {"Content-Type" : COLLECTION_JSON})
        self.assertEquals(resp.status_code, 404)

#415
    def test_patch_wrong_header_media_item(self):
        print '('+self.test_patch_wrong_header_media_item.__name__+')', self.test_patch_wrong_header_media_item.__doc__
        resp = self.client.patch(self.url, data = json.dumps(self.media_patch_correct))
        self.assertEquals(resp.status_code, 415)

#TEST DELETE
#204
    def test_delete_existing_media_item(self):
        print '('+self.test_delete_existing_media_item.__name__+')', self.test_delete_existing_media_item.__doc__
        resp = self.client.delete(self.url, headers = {"Accept" : COLLECTION_JSON})
        self.assertEquals(resp.status_code, 204)

#404
    def test_delete_not_existing_media_item(self):
        print '('+self.test_delete_not_existing_media_item.__name__+')', self.test_delete_not_existing_media_item.__doc__
        resp = self.client.delete(self.url_wrong, headers = {"Accept" : COLLECTION_JSON})
        self.assertEquals(resp.status_code, 404)

if __name__ == '__main__':
    unittest.main()
    print 'Start running tests'