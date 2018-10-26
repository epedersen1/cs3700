README - Project 3


APPROACH

- Packet composition:
  - Data:
    - fragmented chunk of data with a max size of MSS global variable
    - Data is empty if this packet is a termination packet
  - ID:
    - starts at 1, incremented by 1 for each packet containing data
    - termination packet ID = -(max data packet id)
    - arbitrary number for EOF packet
  - Sequence Number (SN): 
    - starts at 0, incremented by the length of the data in the last
      packet sent.
  - End of file (EOF) flag:
    - boolean value indicating if all the data has been sent or not,
      so it is true only for the EOF packets

- ACK composition:
  - ID:
    - equal to the ID of the last data or termination packet received
  - SN:
    - equal to the SN of the last data or termination packet received

- Overview:
  - Sender sends one packet at a time, waiting for an ACK with an
    ID and SN value equivalent to the last packet sent before it
    sends the next packet.
  - receiver gets a packet, checks that it was the expected packet, 
    checks it for data corruption and then sends back an ACK for that
    packet at regular short intervals until it gets the next packet.

- Handling duplicates:
  - Assigned each packet an ID value that starts at 1 for the first
    packet and gets incremented by 1 for each of the following
    packets with data.
  - receiver keeps note of the last packet's ID and if the new packet
    is not the last packet's ID + 1 then it discards the packet as a
    duplicate but still returns an ACK for the duplicated packet so
    that the sender knows it can send the next packet.
    - If the ID is negative then the receiver knows it is a
      termination packet and keeps it, see below

- Handling dropped packets or ACKs:
  - Implemented a TIMEOUT variable for sender
    - sender timeout is used if the first packet is dropped so that
      the sender knows to re-send the packet
  - After the first packet is received, the sender constantly gets 
    duplicate ACKs from receiver (for the last received packet) until
    the receiver has gotten a new packet, in which it will start
    continuously sending the ACK for the new packet.
  - Until the sender gets the first ACK who's ID and SN match the ID 
    and SN of the last packet sent
  - Adjusted our packet size so that it would be large enough to send
    as few packets as possible (to avoid having to wait for timeouts
    constantly in the case of a high drop rate) and small enough so
    that it would not be fragmented by the IP.

- Handling unordered data
  - Not necessary since the sender only sends one packet at a time

- Handling termination:
  - Implemented a TIMEOUT variable for receiver
    - receiver timeout is used to terminate the receiver program in
      the worst case scenario
  - Double handshake system:
    - After sender gets an ACK from the last data packet sent, it
      sends a termination packet (see above in Packet Composition)
    - Receiver gets termination packet and replies with an ACK and
      writes the data packets to the file
    - Sender gets the ACK for the termination packet and sends 3
      identical EOF (see above in Packet Composition) packets where 
      the EOF boolean value = true and then quits.
    - Receiver quits as soon as it recieves at least one EOF packet,
      if none are received then it times out and terminates.

- Error check
  - We implemented a quick error check which would tell us if the
    data had been corrupted by having the receiver use the SN to
    calculate a packet's ID and then check if that ID is = to the 
    actual ID.
  - This check would tell us if the data was longer or shorter than
    it needed to be or if it is the same length and the ID or SN
    had also been corrupted.


CHALLENGES

- Termination challenge:
  - We ran into an issue trying to find a good way for our program to
    terminate while also being sure that all of the data had been
    sent and received.
  - Problem:
    - If sender sent the last packet with data and immediately quit,
      then if this packet dropped, the receiver would not get all of
      the data.
    - If sender waited for ACK from the last packet before quitting 
      and the ACK dropped, the sender would not know if the receiver
      had gotten that packet and quit or if it had not gotten the
      packet at all, so it would timeout and re-send the last data
      packet indefinitely.
  - Solution:
    - Two way handshake (described above, see Handling Termination):
    - Drops in two way handshake model described
      - If termination packet or ACK is dropped, the sender will time 
        out and re-send the termination packet (normal packet drop
        behavior)
      - If the sender only sends 1 EOF packet and it is dropped, 
        receiver can only quit if it times out which is an 
        inefficient solution. To help prevent this inefficiency, we
        have the sender send 3 identical EOF packets before quitting
        to increase the likelyhood of at least one of them getting
        through so that the receiver can quit without timing out.

- We had issues trying to check how performant our program is because
  by the time we got to checking performance, everyone was trying to
  test their programs so the server was very slow regardless.


TEST OVERVIEW
- We ran our code with the test cases, we saw which cases passed and 
  which cases failed. We started doing this by running the starter 
  code with the test cases.
- When we ran the tests, we would focus on the first test case that
  failed and work on implementing a new algorithm that would handle
  this first failed test. Once the new algorithm was implemented, we
  would run the tests again and see if our new algorithm passed the
  intended test (we would run the tests a few times each time we
  checked to be sure that we didn't just get lucky with the tests
  passing). If our new algorithm passed the test, we would move on
  to the next failed test. If not, we would debug or re-write our
  algorithm.
- If the intended test failed with the algorithm we wrote for it, we
  would add print statements and check the output of the test to try
  and solve the flaw in our logic.
- We continued in this manner until all test cases passed.
