p2: pythonshell.py
	cp pythonshell.py p2 && chmod +x p2
clean:
	rm -f p2
test:
	make && ./p2 < test.txt