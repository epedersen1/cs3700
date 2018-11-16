README
Project 4

HIGH LEVEL APPROACH:

Global Variables Explained:
 - DOMAIN             -> website domain used to specify the server address, create GET and POST 
                         messages for GET and POST requests and to verify if we should crawl a 
                         fronteir link
 - PORT               -> specifies the port for the server address
 - USERNAME           -> the username from the args used when calling webcrawler
 - PASSWORD           -> the password from the args used when calling webcrawler
 - THREADS            -> the number of threads used for simultaneous crawling
 - server_address     -> address for connecting sockets
 - socks              -> a dictionary where the keys are thread names and the values are the
                         sockets for the given thread
 - secret_flags_count -> a counter for keeping track of the number of secret keys found so the
                         program doesn't keep searching after all 5 flags are found
 - added              -> dict for keeping track of urls which have already been searched or have 
                         been queued for search. Initialized to the fakebook homepage because
                         queue is initialized to the fakebook homepage
 - queue              -> queue for fronteir urls for threads to search, initialized to fakebook
                         homepage because that is the first page to get searched
 - added_lock         -> thread lock to lock added dict when data needs to be added to it
 - q_lock             -> thread lock to lock queue when a url needs to be added or removed from the
                         queue
 - threads            -> a list of all threads in use so we can later join them
Classes explained:
 - MyHTMLParser       -> class for html parsing which includes a function for setting the 
                         csrf_token and creating a list of links found on a page and a function for
                         printing a secret flag if one is found and incrementing the secret flag 
                         variable.
 - MyThread           -> class for creating a thread with a unique name identifier as well as a
                         queue and added dictionary which are shared amongst all threads and a
                         function for running the thread which just means calling crawl for the
                         thread.
Functions explained: 
 - login              -> takes a thread name and a list of cookies, calls "get" function and uses
                         parser to find csrf token, uses csrf token to build post message, makes a
                         post to fakebook to log in and stores the cookies in the response.
 - get                -> takes a thread name, a url and a list of cookies, builds and sends a get
                         request to fakebook, handles response errors, adds cookies to cookie list,
                         unzips url body if zipped and returns html as a string
 - crawl              -> takes a thread name, queue and added dict, adds a new socket for the given
                         thread to socks and connects the socket, logs into fakebook on the thread,
                         goes down queue parsing the hmtl for each url, adding fronteir links to 
                         queue and added dict and terminating if all 5 flags are found or if queue 
                         is empty.
Algorithm Explained:
 - First we start 50 threads in a loop with a sleep time between each new thread which gets smaller
   and smaller for each new thread. We use sleep because we have to let the first thread populate
   the queue with fronteir urls before the next thread starts, otherwise the queue would be empty
   and the next thread would immidiately terminate. The sleep time can be smaller and smaller with
   each new thread because the queue populates quickly and we don't have to worry about the queue
   emptying too fast.
 - When each thread starts, it calls the crawl function which creates a new socket for the thread,
   adds that socket to the socks dictionary and then connects the given thread's socket to the 
   server. It then initializes a cookies list for that thread which is added to every time cookies
   are found for a url it is making a get or post request to. The cookies are used to make get
   requests as the specified user after login. Crawl then calls login and starts a loop. The loop
   then takes urls off the queue, (using lock when the data in the queue is manipulated), calls
   get on the url to get the HTML of the page, parses the html, adds any fronteir links it finds
   (checking added to see if links are fronteir or not) to the queue and to added (locking added 
   and queue when manipulating data). The loop goes through the queue one URL at a time until 
   either the queue is empty or all 5 secret flags are found.
 - The login function takes a thread name and the thread's cookie list, makes a get request to the
   fakebook homepage, parses the homepage html to get the csrf token which is then used to send a
   post message with the thread's socket and the username and password variables. The response is
   then decoded and split (retrying login if the status code was '500') and new cookies are added
   to the thread's cookie list so the thread can later make get requests as the specified user.
 - The get function builds a message to make a get request to the host of our global domain, the
   given url, the list of cookies as well as flags used to keep the socket connection alive and 
   accept-encoding in the form of gzip (used for efficiency). The thread's socket sends this
   get request and tries to receive the response, handling response status code errors by either
   retrying the request with the same arguments (500), retrying the request with the given redirect
   url (301 or 302) or abandoning url alltogether and returning an empty string (403 or 404). If 
   the response is empty then the socket is closed, redefined and reconnected and get calls itself 
   again with the same arguments to retry. The cookies found in the html are then added to the 
   thread's cookie list, if response is compressed, then it is decompressed. Then the get funtion
   returns the html body decoded.
 - At the end of the program, a for loop is called on the thread list to join all threads which
   forces the program to wait until all threads have completed before terminating. The parse 
   function which is used for the get requests automatically checks for secret flags and if the
   a flag is found it automatically prints it.


CHALLENGES:
 - We didn't have too many challenges on this one, just a bunch of minor bugs that were hard to 
   test because the run time took a while. So it was slow to debug


TESTING OVERVIEW:
 - We tested our program incrementally, first we made a then we made a parser to parse the html. We
   tested this using the homepage, printing the cookies and the csrf token to verify that it
   worked. 
 - Then we made a get function which would send a message to the socket to get the html of a given 
   url. We tested this on the homepage and printed the response to verify that it worked. 
 - Then we made a login function which used the get function and stored the cookies from the 
   response, we used this to verify that our get function worked with cookies on a personal profile
   page.
 - Next we added functionality for accpeting encoded responses and verified that by printing the
   decoded html.
 - Then we added handling for non-200 status codes and verified those by running get with a dummy
   hardcoded response for the first response and print statements in the if statements for the 
   status codes.
 - Then we made our thread class and crawl function, we verified the crawl funciton by running on
   a single thread with a bunch of print statements to verify that it was working properly
 - Then we ran our code with 50 threads and sleep, printing the threads and thread values along
   the way.
 

