import unittest

from context import HandlerMap

class HandlerMapTest(unittest.TestCase):

    TEST_HANDLER="thing"
    TEST_HANDLER2="Otherthing"

    def test_single_name_part(self):
        fixture = HandlerMap()
        fixture.register_handler("VOLTAGE",self.TEST_HANDLER)
        self.assertEqual(fixture.find_handler("VOLTAGE"),self.TEST_HANDLER)

    def test_compound_name_part(self):
        fixture = HandlerMap()
        fixture.register_handler("VOLTAGE:SOURCE",self.TEST_HANDLER)
        self.assertEqual(fixture.find_handler("VOLTAGE:SOURCE"),self.TEST_HANDLER)

    def test_compound_name_part_lower(self):
        fixture = HandlerMap()
        fixture.register_handler("VOLTAGE:SOURCE",self.TEST_HANDLER)
        self.assertEqual(fixture.find_handler("voltage:source"),self.TEST_HANDLER)

    def test_multiple(self):
        fixture = HandlerMap()
        fixture.register_handler("VOLTAGE:SOURCE:SET",self.TEST_HANDLER)
        fixture.register_handler("VOLTAGE:SOURCE",self.TEST_HANDLER2)
        self.assertEqual(fixture.find_handler("voltage:source"),self.TEST_HANDLER2)
        self.assertEqual(fixture.find_handler("voltage:source:set"),self.TEST_HANDLER)

    def test_compound_name_with_shorts(self):
        fixture = HandlerMap()
        fixture.register_handler("VOLTage:SOUrce",self.TEST_HANDLER)
        self.assertEqual(fixture.find_handler("VOLTAGE:SOURCE"),self.TEST_HANDLER)
        self.assertEqual(fixture.find_handler("voltage:source"),self.TEST_HANDLER)
        self.assertEqual(fixture.find_handler("VOLTage:SOUrce"),self.TEST_HANDLER)
        self.assertEqual(fixture.find_handler("VOLT:SOU"),self.TEST_HANDLER)
        self.assertEqual(fixture.find_handler("volt:sou"),self.TEST_HANDLER)


if __name__ == '__main__':
    unittest.main()
