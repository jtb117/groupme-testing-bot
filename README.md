# GroupMe Chat Bot
Offers utility and data analysis

Commands must follow "@bot" to be recognized
Implemented features:
  * !all - Mention all users in the chat.
  * !remember {trigger}::{response} - The bot will send a message identical to *response* when a message identical to *trigger* is sent.
  * !forget {trigger} - The *trigger* will no longer prompt *response*
  * !triggers - Returns a list of saved triggers.
  * Unrecognied command - Bot will respond "Huh?" to indicate the command is not recognized.
  
Upcoming features:
  * !message-count - Returns a graph of message counts by user.
  * !update-data - Updates the S3 bucket file containing the chat's history.
  * !random-pic {threshold} {start date} {end date} - Returns a random image with likes greater than or equal to the *threshold* within the date range.
  * !render-chat {threshold} {start date} {end date} - Returns a link to a static site which mimics GroupMe's UI containing a pseudo history containing messages above the *threshold* and within the date range. 
  * !pinned - Displays the pinned messages
  * !add-pinned {message} - The *message* will be added to the pinned list.
  * !drop-pinned {index} - Remove a message from the pinned list with the given *index*.
