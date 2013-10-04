MWEL ("MWorks Experiment Language")
===================================



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

Global name bindings are created by assigning a value to a name that has not previously been declared local in the current scope or any enclosing scope.  

TODO:  Are global names global program-wide or just within the current module?



Functions
---------

A function definition statement can appear in any statement list.  It both creates the function and binds it to a name.  If "function" is preceded by "local", then the binding is local to the current scope.  Otherwise, the binding is global.

An inline function definition (i.e. function definition expression) creates a function but does not bind it to a name.

As in Lua, functions are first-class values with proper lexical scoping.  As such, the body of a function can access local names from all enclosing local scopes (including any enclosing function definitions).

When a function created by a function definition statement or expression is called, its arguments are all evalutated and bound to local names within the function body, and then the body is executed.

When a builtin function is called, it receives all its arguments (including all elements of the call statement body) as *unevaluated* expressions.  This allows the function to defer evaluation, selectively evaluate arguments, and/or inspect the AST.  (This is necessary because all control-flow constructs are implemented as functions.)



Modules
-------

TODO:  I'm thinking Python-style modules, i.e. the contents a single source file.  These would be "require"-able from other modules (loaded at most once per session).  Should loading a module add its global names to the program-wide global scope, or should the "require" call return an object with attributes for each of its global names?
