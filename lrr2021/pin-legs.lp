% The pace slack minimization objective didn't end up having much influence
% when competing with other criteria. We'll designate some fast legs manually.
assignment(("Ellis"; "Nick"), leg(0,0,1)).
assignment("Johanna", leg(2,2,3)).
assignment("Jamie", (leg(14,14,15);leg(15,15,16);leg(16,16,17);leg(17,17,18))).

% Allow for post-leg walk
%assignment("Reshabh", leg(11, 11, 12)).

% Pike Place walk leg
%assignment("Vishwas", leg(12, 12, 13)).


% Pin announced starts
%assignment("Yuxuan", leg(3, 3, 4)).
%assignment(("Brett";"James";"Jennifer";"Lancelot";"Max";"Sameer";"Sidd";"Swati";"Yuxuan";"Zach"),leg(4,4,5)).
%assignment(("Brett"; "James";"Jennifer";"Lancelot";"Max";"Sameer";"Sidd";"Swati";"Yuxuan";"Zach"),leg(5,5,6)).
% Shift off walk leg
%assignment("Jingwei", leg(9,9,10)).
%assignment("Pratyush", leg(9,9,10)).

%assignment("Chandra", leg(11, 11, 12)).
%assignment("Amal", leg(15,15,16)).
%assignment("Chandra", leg(17,17,18)).

% Needs a later start
assignment("Edward", leg(14,14,15)).


% Location exclusions
:- exchangeVisit("Jennifer", 11).

:- not strollerTraversible(S1, S2), assignment("Maya", leg(T,S1,S2)), legTime(T).