% Only strollable option
run_leg("Maya", leg(15, 3, 2)).
run_leg("Maya", leg(16, 2, 1)).

% The pace slack minimization objective didn't end up having much influence
% when competing with other criteria. We'll designate some fast legs manually.
run_leg(("Ellis"; "Nick"), leg(0,18,17)).
run_leg("Johanna", leg(2,16,15)).
run_leg("Jamie", (leg(14,4,3);leg(15,3,2);leg(16,2,1);leg(17,1,0))).

% Allow for post-leg walk
run_leg("Reshabh", leg(11, 7, 6)).

% Pike Place walk leg
run_leg("Vishwas", leg(12, 6, 5)).


% Pin announced starts
run_leg("Yuxuan", leg(3, 15, 14)).
run_leg(("Brett";"James";"Jennifer";"Lancelot";"Max";"Sameer";"Sidd";"Swati";"Yuxuan";"Zach"),leg(4,14,13)).
run_leg(("Brett"; "James";"Jennifer";"Lancelot";"Max";"Sameer";"Sidd";"Swati";"Yuxuan";"Zach"),leg(5,13,12)).
% Shift off walk leg
run_leg("Jingwei", leg(9,9,8)).
run_leg("Pratyush", leg(9,9,8)).

run_leg("Chandra", leg(11, 7, 6)).
run_leg("Amal", leg(15,3,2)).
run_leg("Chandra", leg(17,1,0)).

% Needs a later start
run_leg("Edward", leg(14,4,3)).
