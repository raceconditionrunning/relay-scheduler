elem(window, window, root).
attr(window, child_layout, flex).
attr(window, flex_direction, column).
%%%%%%%%%%%%%%%%%
elem(menu_bar, menu_bar, window).
attr(menu_bar, title, "Relay Scheduling").
attr(menu_bar, icon, "fa-running").

elem(menu_bar_next, button, menu_bar).
attr(menu_bar_next, label, "Next").
attr(menu_bar_next, icon, "fa-forward-step").
when(menu_bar_next, click, call, next_solution(opt)).

elem(cost_summary, container, window).
attr(cost_summary, order, 1).
attr(cost_summary, child_layout, flex).
attr(cost_summary, flex_direction, row).
elem(cost_summary(Index), container, cost_summary) :- _clinguin_cost(Index, Cost).
attr(cost_summary(Index), order, Index) :- _clinguin_cost(Index, Cost).
elem(cost_summary_label(Index), label, cost_summary(Index)) :- _clinguin_cost(Index, Cost).

attr(cost_summary_label(Index), label, @concat(CostName, ": ", Cost)) :- _clinguin_cost(Index, Cost), objective(Index, CostName).
%%%%%%%%%
elem(workarea, container, window).
attr(workarea, child_layout, flex).
attr(workarea, flex_direction, row).
attr(workarea, order, 2).
elem(participants, container, workarea).

%%%%%%%%%
elem(add_person, button, participants).
attr(add_person, order, -1).
attr(add_person, label, "Add Runner").
attr(add_person, icon, "fa-user-plus").
attr(add_person, class, ("btn-info";"m-2")).
when(add_person, click, update, (add_modal, visibility, shown)).

elem(add_modal, modal, window).
attr(add_modal, title, "Add Runner").
elem(modal_content, container, add_modal).
attr(modal_content, class, ("d-flex";"flex-column")).

elem(name_tf, textfield, modal_content).
attr(name_tf, placeholder, "Name").
attr(name_tf, order, 1).
attr(name_tf, width, 250).
when(name_tf, input, context, (name, _value)).

elem(distance_tf, textfield, modal_content).
attr(distance_tf, placeholder, "Preferred distance (in miles)").
attr(distance_tf, order, 2).
attr(distance_tf, width, 250).
when(distance_tf, input, context, (distance, _value)).

elem(pace_tf, textfield, modal_content).
attr(pace_tf, placeholder, "Preferred pace (10:00)").
attr(pace_tf, order, 3).
attr(pace_tf, width, 250).
when(pace_tf, input, context, (pace, _value)).

elem(b1, button, modal_content).
when(b1, click, call, add_atom(participant(_context_value(name,str)))).
when(b1, click, call, add_atom_transform(preferredDistance(_context_value(name,str), _context_value(distance,str)))).
when(b1, click, call, add_atom(preferredDistanceStr(_context_value(name,str), _context_value(distance,str)))).
when(b1, click, call, add_atom_transform(preferredPace(_context_value(name,str), _context_value(distance,str)))).

attr(b1, order, 4).
attr(b1, label, "Add").
attr(b1, class, "m-1").
attr(b1, class, "btn-secondary").
attr(b1, icon, "fa-plus").


%%%%%%%%%%
elem(participant(P), container, participants):- participant(P).
attr(participant(P), order, P):- participant(P).
attr(participant(P), width, 400):- participant(P).
attr(participant(P), class, ("bg-primary";"bg-opacity-25";"rounded";
                       "d-flex";"flex-column";"align-items-start";
                       "p-3";"m-3"
                     )):- participant(P).

elem(participant_label(P), label, participant(P)):- participant(P).
attr(participant_label(P), order, 1):- participant(P).
attr(participant_label(P), label, @concat("","",P)):- participant(P).
elem(participant_leg_label(P, StartExchange, EndExchange), label, participant(P)):- startExchange(P, StartExchange), endExchange(P, EndExchange), participant(P).
attr(participant_leg_label(P, StartExchange, EndExchange), order, 2):- startExchange(P, StartExchange), endExchange(P, EndExchange), participant(P).
attr(participant_leg_label(P, StartExchange, EndExchange), label, @concat(StartName," -> ",EndName)):- exchangeName(StartExchange, StartName), exchangeName(EndExchange, EndName), startExchange(P, StartExchange), endExchange(P, EndExchange), participant(P).

elem(leg_c((P,C)), container, participant(P)):- participant(P), C=1..2.
attr(leg_c((P,C)), order, C+3):- participant(P), C=1..2.
attr(leg_c((P,C)), class, ("d-flex";"flex-row")):- participant(P), C=1..2.
elem(leg_label((P,C)), label, leg_c((P,C))):- participant(P), C=1..2.
attr(leg_label((P,C)), order, 1):- participant(P), C=1..2.
attr(leg_label((P,1)), label, "Start Exchange"):- participant(P).
attr(leg_label((P,2)), label, "End Exchange"):- participant(P).
elem(leg_dd((P,C)), dropdown_menu, leg_c((P,C))):- participant(P), C=1..2.
attr(leg_dd((P,C)), order, 2):- participant(P), C=1..2.
attr(leg_dd((P,C)), class, ("btn-sm";"btn-primary";"m-2")):- participant(P), C=1..2.
attr(leg_dd((P,1)), selected, N):- _clinguin_assume(startExchange(P, StartExchange),true), exchangeName(StartExchange, N).
attr(leg_dd((P,2)), selected, N):- _clinguin_assume(endExchange(P, EndExchange),true), exchangeName(EndExchange, N).
% Classes applied to the button, not the container around the menu items.
attr(leg_dd((P,C)), class, ("d-flex";"flex-column")):- participant(P), C=1..2.
attr(leg_dd((P,1)), label, "Start Exchange"):- participant(P).
attr(leg_dd((P,2)), label, "End Exchange"):- participant(P).

elem(leg_ddi((P,C),remove), dropdown_menu_item, leg_dd((P,C))):- participant(P), C=1..2.
attr(leg_ddi((P,C),remove), order, 0):- participant(P), C=1..2.
attr(leg_ddi((P,C),remove), label, "-"):- participant(P), C=1..2.
when(leg_ddi((P,1),remove), click, call, remove_assumption_signature(startExchange(P, any))):- participant(P).
when(leg_ddi((P,2),remove), click, call, remove_assumption_signature(endExchange(P, any))):- participant(P).

elem(leg_ddi((P,1), StartExchange), dropdown_menu_item, leg_dd((P,1))):- leg(Start, StartExchange, _), participant(P).
elem(leg_ddi((P,2), EndExchange), dropdown_menu_item, leg_dd((P,2))):- leg(Start, _, EndExchange), participant(P).
% Order doesn't apply because menu isn't displayed "flex"
attr(leg_ddi((P,1), StartExchange), order, Start):- leg(Start, StartExchange, _), participant(P).
attr(leg_ddi((P,2), EndExchange), order, Start):- leg(Start, _, EndExchange), participant(P).

attr(leg_ddi((P,1),StartExchange), label, N):- leg(Start, StartExchange, _), participant(P), exchangeName(StartExchange, N).
attr(leg_ddi((P,2),EndExchange), label, N):- leg(Start, _, EndExchange), participant(P), exchangeName(EndExchange, N).
when(leg_ddi((P,1),StartExchange), click, call, remove_assumption(startExchange(P, StartExchange'))):-
                     participant(P), leg(Start, StartExchange, _), _clinguin_assume(startExchange(P, StartExchange'),true), StartExchange!=StartExchange'.
when(leg_ddi((P,2),EndExchange), click, call, remove_assumption(endExchange(P, EndExchange'))):-
                     participant(P), leg(Start, _, EndExchange), _clinguin_assume(endExchange(P, EndExchange'),true), EndExchange!=EndExchange'.
when(leg_ddi((P,1),StartExchange), click, call, add_assumption(startExchange(P, StartExchange),true)):-
                     participant(P), leg(Start, StartExchange, _).
when(leg_ddi((P,2),EndExchange), click, call, add_assumption(endExchange(P, EndExchange),true)):-
                     participant(P), leg(Start, _, EndExchange).

elem(lead_cb(P), checkbox, participant(P)):- participant(P).
attr(lead_cb(P), order, 5):- participant(P).
attr(lead_cb(P), label, "willing to lead"):- participant(P).
attr(lead_cb(P), checked, true):- willingToLead(P).
when(lead_cb(P), click, call, add_atom(willingToLead(P))):- not willingToLead(P), participant(P).
when(lead_cb(P), click, call, remove_atom(willingToLead(P))):- willingToLead(P).


%%------------------------------
%% Assignments
%% -----------------------------
elem(legs, container, workarea).

elem(leg(T, StartExchange, EndExchange), container, legs):- leg(T, StartExchange, EndExchange).
attr(leg(T, StartExchange, EndExchange), order, T):- leg(T, StartExchange, EndExchange).
attr(leg(T, StartExchange, EndExchange), width, 600):- leg(T, StartExchange, EndExchange).
attr(leg(T, StartExchange, EndExchange), class, ("bg-primary";"bg-opacity-25";"rounded";
                       "d-flex";"flex-column";"align-items-start";
                       "p-2";"m-2"
                     )):- leg(T, StartExchange, EndExchange).

 elem(leg_label(T, StartExchange, EndExchange), label, leg(T, StartExchange, EndExchange)):- leg(T, StartExchange, EndExchange).
 attr(leg_label(T, StartExchange, EndExchange), label, @concat(StartName," -> ",EndName)):- exchangeName(StartExchange, StartName), exchangeName(EndExchange, EndName), leg(T, StartExchange, EndExchange).

elem(assignment_label(P, leg(T, StartExchange, EndExchange)), label, leg(T, StartExchange, EndExchange)):- assignment(P, leg(T, StartExchange, EndExchange)).
attr(assignment_label(P, leg(T, StartExchange, EndExchange)), order, P):- assignment(P, leg(T, StartExchange, EndExchange)).
attr(assignment_label(P, leg(T, StartExchange, EndExchange)), label, @concat("",P)):- assignment(P, leg(T, StartExchange, EndExchange)).
