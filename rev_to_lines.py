def rev_to_line(revs,knob):
	degrees=revs*360
	# knob=0 if you are working with x or y knob
	if knob==0:
		lines=degrees/21.82
	# knob=1 if you are working with x or y knob
	if knob==1:
		lines=degrees/15.652
	return(lines)

