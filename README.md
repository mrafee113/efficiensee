### Description
This project was an attempt to note down and eventually monitor my productivity measure with time better.  
But VPNs got banned, so I stopped using it. I have to come up with a way to replace Gsheets.  

The way this works is, you create a google sheets doc and structure as I've done in mine.
I should add it here. Then when you run the django command `prodify`, it will fetch the
data of the day (should be ran at the end of the day), and store it in postgres.
Then it will aggregate the results so far (I think for the past 3 months or so),
and update the aggregation section of the sheet. So you can monitor your progress,
which acts as a good align-er towards your path. THAT IS, if you can use it.  

I wanted to use excel but there's no way to use it on my phone. With sheets, you can
create a shortcut. And I don't have and probably for now will not, acquire android 
development skills.  

### TODOS
- add link to a template sheets structure
- cleanup
- write todos
