% Only strollable option
run_leg("Maya", leg(15, 3, 2)).
run_leg("Maya", leg(16, 2, 1)).

% The pace slack minimization objective didn't end up having much influence
% when competing with other criteria. We'll designate some fast legs manually.
run_leg("Ellis", leg(0,18,17)).
run_leg("Johanna", leg(2,16,15)).
run_leg("Jamie", (leg(15,3,2);leg(16,2,1);leg(17,1,0))).

% Allow for post-leg walk
run_leg("Reshabh", leg(11, 7, 6)).

% Pike Place walk leg
run_leg("Vishwas", leg(12, 6, 5)).
