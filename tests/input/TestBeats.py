import mock

from tests.ModuleBaseTestCase import ModuleBaseTestCase
from lumbermill.input import Beats


class TestBeats(ModuleBaseTestCase):

    def setUp(self):
        super(TestBeatsInput, self).setUp(Beats.Beats(mock.Mock()))



    def tearDown(self):
        self.test_object.shutDown()
        ModuleBaseTestCase.tearDown(self)