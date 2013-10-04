JEL ("JSON Expression Language")
================================



Identifiers
-----------

Variable and function identifiers are case sensitive and consist of a letter (A-Z, a-z) or underscore followed by zero or more letters, digits (0-9), and/or underscores.



Data Types
----------

Null:  null
Boolean:  true, false
Number:  2, -3.4, 10.3e18, 12ms
String:  "foo", "foo bar", 'baz', "", ''
List:  [2, "foo", true], [1,2,], []
Dictionary: {"a":1, "b":2, c:"foo", "1 2 3":"bar"}, {'x': null,}, {}


All values are immutable.

Number literals can include a unit suffix.  A unit suffix consists of a letter (A-Z, a-z), followed by one or more letters or digits (0-9).  The suffix is interpreted as a scaling factor for the preceding number; the parser will query the embedding application for the appropriate scale factor and then multiply the preceding number by it.  For example, if the base time unit for an application is microseconds, then the scale factor for the unit suffix "ms" (denoting milliseconds) is 1000, and the literal 5ms is eqivalent to 5000.

Strings are Unicode.

Dictionary keys must be strings.  As in JavaScript, if a key is a valid identifier, then the quotes around it may be omitted.  Because of this, key names in dictionary literals must always be literal strings (i.e. they can't be arbitrary expressions as in Python).  However, the associated values can be any expression.

Every valid JSON document is a valid JEL expression (i.e. JEL is a proper superset of JSON).  Every JEL value can be serialized as a JSON document (importantly, with no loss of type info).



Operators
---------

From highest to lowest precedence:

(expression)                       Subexpression
x[index], x(args...), x.name       Indexing, function call, attribute access
**                                 Exponentiation
+x, -x                             Positive, negative
*, /, %                            Multiplication, division, remainder
+, -                               Addition, subtraction
<, <=, >, >=, !=, ==, in, not in   Comparisons
not x                              Logical NOT
and                                Logical AND
or                                 Logical OR


Logical operators always return a boolean value (i.e. true or false).  Every data type has a truth value and can be used as an operand to a logical operator.

Comparison operators are chained as in Python.  That is, `x < y < z` is equivalent to `(x < y) and (y < z)`.  The result of a comparision chain is always a boolean.

Every data type can be tested for (in)equality with any other data type.  Values of different types always compare not equal.  However, ordering comparisons are *not* valid between different data types.

As in Python, exponentiation groups from right to left.  That is, 2**3**4 is equivalent to 2**(3**4), not (2**3)**4.

Only dictionaries support attribute access, and only for keys that are valid identifiers.  For example, if dictionary d has key 'abc123', then d.abc123 is equivalent to d['abc123'].

JEL doesn't currently support C-style bitwise operators (|, ^, &, <<, >>), but it might in the future.  Since C-style AND and OR (&&, ||) are easily confused with bitwise AND and OR (&, |), JEL eschews the former and instead adopts Python-style 'and' and 'or'.
