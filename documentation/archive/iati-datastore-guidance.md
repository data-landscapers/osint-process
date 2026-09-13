I think the most robust way to find new activities would be for you to keep a cached copy of the list of all known activity identifiers, and then every time you want to run an update (every 9 days), re-pull the entire list of activity IDs and see which ones are new.
 
You can pull the entire list very easily using the IATI Datastore API: search for '*:*' and limit the output to the iati_identifier field so that only the activity identifier is returned. There are 940k records so you'll have to use paging in the API queries, but the entire output would be less than 1 Mb. 
 
You can also include the iati_activities_document_id field, which is the globally unique id for the dataset which the activity came from. This would allow you to identify the source URL, if needed, by using that document ID to lookup the dataset details in one of the outputs from the Bulk Data Service (e.g. https://bulk-data.iatistandard.org/datasets-minimal).
 
Once you've got the list of new activity identifiers, you can then pull their full record from the Datastore API, or, by looking up the source dataset, you could extract the XML directly from the file if you're also storing a copy of all the raw XML.
 
The full Solr query would be something like (this pulls the first 1000 records):
 

curl -v -X GET "https://api.iatistandard.org/datastore/activity/select?q=*:*&rows=1000&fl=iati_identifier,%20iati_activities_document_id&wt=json" -H "Cache-Control: no-cache" -H "Ocp-Apim-Subscription-Key: API_KEY_HERE"
 
The Datastore API is Solr, so Claude will know how to interact with it, and will be able to optimise the query if you point it at the Developer docs. 
 
This would only get you new activities. It would be a bit trickier to find updated activities because there isn't yet a marker which provides a unique reference to each version of the activity. The way to find updated activities would be to include the iati_activities_document_hash as one of the fields output by the Datastore Solr query you run. That value is a hash of the whole XML dataset/file. When the hash changes, you know that the contents of the file has changed, so you know that at least one activity in the file/dataset has changed, but not which one(s). To find which activities have been updated, you'd need to store a hash of each activity alongside the activity identifier. This would require pulling the full XML for each activity - but you'd only need to do this the first time you see the activity, and then subsequently only when the iati_activities_document_hash indicates that the dataset containing the activity has changed. This is not ideal, since some datasets contain thousands of activities, and so if one of those datasets updates a single activity, you'd be checking thousands of activities just to find one updated one. But it is very workable. Instead of pulling the XML for each activity from the Datastore API, you could just have the pipeline download the XML for the entire IATI corpus at the start of each run using the bulk ZIP provided by the Bulk Data Service (see https://bulk-data.iatistandard.org/) - then you've got it all on disk and could extract individual activities very quickly to create the hashes using the source XML.
 
One caveat: the Datastore cleans and fixes the XML in some cases, so when creating a hash of the individual activities, you'd either need to always use the XML from the Datastore or the XML extracted from the source files - you wouldn't be able to compare hashes from the two sources.
