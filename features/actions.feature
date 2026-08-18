Feature: Actions
	As a user of the Rupert Audio Player
	I want to be able to play a playlist of tracks
	So that I can enjoy my music without having to manually select each track

	Scenario: Send a action
		Given a request for /api/action/testing/simple
		When we process the request
		Then a message should be sent to the flask.testing topic
		Then the response should contain "Action received: testing/simple"
	
