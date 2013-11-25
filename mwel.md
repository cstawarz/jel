MWorks Experiment Language (MWEL)
=================================



Values
------

All values created by literal expressions are immutable.  Other values (i.e. predefined or obtained via function calls) may or may not be mutable.



Assignment
----------

Valid assignment targets are identifiers, attribute expressions, and subscript expressions.

Assignment to an identifier binds a value to a name.  Global names can be bound only once.  Local names can be rebound at any time.

Assignment to a subscript or attribute expression mutates the target of the expression (or raises an error if the target is immutable).



Scope
-----

Names can have global or local scope.

Every statement list (i.e. the top level of a module, and the bodies of call and function definition statements) gets its own local scope.  Local scopes nest lexically, and local names mask identical names in the global scope or enclosing local scopes.

Local names are created by prefixing an assignment-to-identifier statement with the "local" keyword, e.g.

    local x = 5

Within a given statement list, a name can be declared local only once.  That is, the following is invalid:

    local x = 1
    ...
    local x = 2

However, this is fine:

    local x = 1
    ...
    if (...):
        local x = 2  # Masks x in enclosing scope
        ...
    end

Global name bindings can be created only at the top level of a module (i.e. not from within a function).  A global name binding is created by assigning a value to a name that has not previously been declared local.

TODO:  Are global names global program-wide or just within the current module?



Functions
---------

A function definition statement can appear in any statement list.  It both creates the function and binds it to a name.  If "function" is preceded by "local", then the binding is local to the current scope.  Otherwise, the binding is global.

An inline function definition (i.e. function definition expression) creates a function but does not bind it to a name.

As in Lua, functions are first-class values with proper lexical scoping.  As such, the body of a function can access local names from all enclosing local scopes (including any enclosing function definitions).

When a function created by a function definition statement or expression is called, its arguments are all evalutated and bound to local names within the function body, and then the body is executed.

When a builtin function is called, it receives all its arguments (including the call statement body) as *unevaluated* executable code.  This allows the function to defer evaluation and/or selectively evaluate arguments.  (This is necessary because all control-flow constructs are implemented as functions.)



Call Statments
--------------

Call expressions (i.e. simple call statements) may be used as call statements only if they return null.  Otherwise, they must be the right-hand side of an assignment statement.  (Put another way:  Call expression results cannot be silently discarded.)  This is to prevent users from forgetting to bind the results of object-constructor calls to names.  (TODO:  Support assignment to "_" as a means of explicitly discarding call expression results?)

Compound call statements (i.e. those with a statement body) are not expressions and cannot return a result.

Compound call statements can add local names to the environment in which their body statements execute.  For example, "while" could add a local "break" function that terminates execution of the body and exits the loop.  Similarly, "trial" could add local functions for accepting/rejecting selections.



Modules
-------

TODO:  I'm thinking Python-style modules, i.e. the contents of a single source file.  These would be "require"-able from other modules (loaded at most once per session).  Should loading a module add its global names to the program-wide global scope, or should the "require" call return an object with attributes for each of its global names?  Maybe it would be best to follow Lua and support both options, with "object-like" modules ending with a top-level return statement.
