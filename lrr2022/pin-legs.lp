% Accommodate pacing
:- not assignmentRange("Lauren", legRange(8, 12)).

% Wants to start
:- not exchangeVisit("Ellis", 0).

% Needs to start
:- not exchangeVisit("Nick", 0).


% Strollable
:- not strollerTraversible(S1, S2), assignment("Maya", leg(T,S1,S2)), legTime(T).
