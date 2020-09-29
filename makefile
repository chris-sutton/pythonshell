p3: pythonshell.py
	cp pythonshell.py p3 && chmod +x p3
clean:
	rm -f p3
test:
	make && ./p3 < test.txt