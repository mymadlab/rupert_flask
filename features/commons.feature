Feature: Common/shared functionality

	Scenario: Open a configuration file
		Given a configuration file is passed at start up
		When we open the configuration file
		Then the configuration file should be loaded
	 
	Scenario: Check hello world
		Given a request for hello
		When we process the request
		Then text returned should contain "Hello World!"
	
	Scenario: Save a JSON file
		Given a JSON file needs to be saved
		When we save the JSON file
		Then the JSON file should be saved
	
