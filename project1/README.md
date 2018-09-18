Mustafa Camurcu
Eliza Pedersen

Project 1

	After reading the prompt, we first looked into python server 
libraries to see if we could use python to complete the assignment.
After finding suitable documentation, we created a shell script to 
accept the command that would run the program with the appropriate
arguments. We then used the python socket library to define a
socket and connect to it with the given port and IP address from the
arguments. We printed the response to determine if we were able to
connect and it worked! Afterwards we made a while loop to count the
characters in the FIND messages, using "\n" to determine if there
was a new message or if the next string was part of the last message
that just overflowed the buffer. We put a check to see if the message
was a "BYE" message and if so, break the while loop after printing
the secret keys. 
	We had a minor issue in forgetting to reset the message
variable to an empty string at the end of the loop which was causing
a bug. Otherwise, it was smooth sailing.
	We tested the code by connecting to the server and verifying
that it returned the same student ID that we gave it along with the
find and bye messages. We also made sure that it returned a secret 
key and not an error message.
