% Accommodate pacing
assignment("Lauren", leg(8, 8, 9)).
assignment("Lauren", leg(9, 9, 10)).
assignment("Lauren", leg(10, 10, 11)).
assignment("Lauren", leg(11, 11, 12)).
assignment("Lauren", leg(12, 12, 13)).

% Wants to start
:- not exchangeVisit("Ellis", 0).

% Needs to start
:- not exchangeVisit("Nick", 0).


% Strollable
:- not strollerTraversible(S1, S2), assignment("Maya", leg(T,S1,S2)), legTime(T).
