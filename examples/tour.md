# Markdown Support: Inline

* Styling
    * *italic*
    * **bold**
    * ***bold underline***
* Inline `code`

---

# Markdown Support: Code Blocks

Code blocks with language syntax highlighting

~~~python
def a_function(arg1, arg2):
    """This is a function
    """
    print(arg1)
~~~

---

# Markdown Support: Lists

* Top level
    * Level 2
        * Level 3
            * Level 4
    * Level 2
        * Level 3
            * Level 4
    * Level 2
        * Level 3
            * Level 4


---

# Embeddable Terminals

Terminals can be embedded directly into slides!

The markdown below:

~~~md
```terminal8
bash -il
```
~~~

becomes

```terminal8
bash -il
```

---

# Embeddable Terminals: Docker containers

Want to drop directly into a docker container for a clean environment
in the middle of a slide?

~~~md
```terminal8
docker run --rm -it ubuntu:18.04
```
~~~

```terminal8
docker run --rm -it ubuntu:18.04
```

---

# Embeddable Terminals: Asciinema Replays

Asciinema is an awesome tool for recording and sharing terminal commands.
If you have asciinema installed (`pip install asciinema`), play back a
pre-recorded shell session inside of a slide!

~~~md
```terminal8
asciinema play https://asciinema.org/a/232377
```
~~~

```terminal40
asciinema play https://asciinema.org/a/232377
```
